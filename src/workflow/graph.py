from langgraph.graph import StateGraph, END
from typing import Dict, Any
from src.workflow.state import WorkflowState
from src.workflow.agents.planner import PlannerAgent
from src.workflow.agents.plan_specer import PlanSpecerAgent
from src.workflow.agents.content_quality import ContentQualityAgent
from src.workflow.agents.slide_packet_builder import SlidePacketBuilderAgent
from src.workflow.agents.direct_bullet_writer import DirectBulletWriterAgent
from src.utils.config import Config

def create_workflow() -> StateGraph:
    workflow = StateGraph(WorkflowState)
    planner = PlannerAgent(Config.LLM_MODEL_NAME)
    content_quality = ContentQualityAgent(Config.LLM_MODEL_NAME)
    packet_builder = SlidePacketBuilderAgent(Config.LLM_MODEL_NAME)
    bullet_writer = DirectBulletWriterAgent(Config.LLM_MODEL_NAME)
    plan_specer = PlanSpecerAgent(Config.LLM_MODEL_NAME)

    def planner_node(state: WorkflowState) -> Dict[str, Any]:
        print(f"\n{'=' * 60}")
        print(f' Planner — Generating initial outline with goals...')
        print(f"{'=' * 60}\n")
        plan = planner.create_outline(state['document_context'])
        lecture_title = planner.generate_title(plan['outline'], state['document_context'])
        try:
            print(f'\nGenerated lecture title: {lecture_title}\n')
        except UnicodeEncodeError:
            print('\nGenerated lecture title: [unicode title]\n')
        return {'lecture_plan': plan, 'lecture_title': lecture_title, 'slides': []}

    def plan_specer_node(state: WorkflowState) -> Dict[str, Any]:
        outline_md = state['lecture_plan']['outline']
        print(f"\n{'=' * 60}")
        print(f' Plan Specer — Specifying slide specs from outline...')
        print(f"{'=' * 60}\n")
        specs = plan_specer.specify(outline_md, state['document_context'])
        if not specs:
            raise RuntimeError('Plan Specer produced 0 slide specs from the outline.')
        return {'slide_specs': specs}

    def packet_builder_node(state: WorkflowState) -> Dict[str, Any]:
        slide_specs = state.get('slide_specs', [])
        print(f'  Packet Builder — creating {len(slide_specs)} source-grounded slide packet(s)...')
        packets = packet_builder.build_packets(slide_specs=slide_specs, context=state['document_context'])
        return {'slide_packets': packets}

    def direct_bullet_writer_node(state: WorkflowState) -> Dict[str, Any]:
        packets = state.get('slide_packets', [])
        print(f'  Direct Bullet Writer — generating {len(packets)} final slide(s) from packets...')
        slides = bullet_writer.write(packets=packets, slide_specs=state.get('slide_specs', []))
        return {'slides': slides}

    def content_quality_node(state: WorkflowState) -> Dict[str, Any]:
        print(f"\n{'=' * 60}")
        print(f' Content QA — Checking slide substance and title alignment...')
        print(f"{'=' * 60}\n")
        repaired_slides, qa_report = content_quality.repair_with_report(
            state['slides'],
            state.get('slide_specs', []),
            state['document_context'],
            slide_packets=state.get('slide_packets', []),
        )
        return {'slides': repaired_slides, 'qa_report': qa_report}

    workflow.add_node('planner', planner_node)
    workflow.add_node('plan_specer', plan_specer_node)
    workflow.add_node('packet_builder', packet_builder_node)
    workflow.add_node('direct_bullet_writer', direct_bullet_writer_node)
    workflow.add_node('content_quality', content_quality_node)

    workflow.set_entry_point('planner')
    workflow.add_edge('planner', 'plan_specer')
    workflow.add_edge('plan_specer', 'packet_builder')
    workflow.add_edge('packet_builder', 'direct_bullet_writer')
    workflow.add_edge('direct_bullet_writer', 'content_quality')
    workflow.add_edge('content_quality', END)
    return workflow.compile()
