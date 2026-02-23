D:.
│   .env
│   .env.example
│   .gitignore
│   main.py
│   PROJECT.md
│   README.md
│   requirements.txt
│   setup.bat
│
├───data
│   ├───assets
│   │       .gitkeep
│   │
│   ├───context
│   │       .gitkeep
│   │
│   ├───optimization
│   │       .gitkeep
│   │
│   ├───raw
│   │       .gitkeep
│   │
│   └───templates
│       ├───dark_modern
│       │       cards.md
│       │       code.md
│       │       comparison.md
│       │       config.json
│       │       formula.md
│       │       hero.md
│       │       split_image_list.md
│       │       stats.md
│       │       table.md
│       │       thankyou.md
│       │       timeline.md
│       │       visual.md
│       │
│       ├───light_minimal
│       │       config.json
│       │
│       └───multi-agent
│               config.json
│
├───images
│       Lecture-gen-2025-12-31.png
│
├───pinkyne_extension
│   │   pinkyne_client.py
│   │   pinkyne_config.py
│   │   pinkyne_langchain.py
│   │   QUICKSTART.md
│   │   quick_start.py
│   │   README.md
│   │   setup_pinkyne.py
│   │   test_api.py
│   │   __init__.py
│   │
│   └───__pycache__
│           pinkyne_client.cpython-313.pyc
│           pinkyne_config.cpython-313.pyc
│           pinkyne_langchain.cpython-313.pyc
│           __init__.cpython-313.pyc
│
├───slidev
│   │   .gitignore
│   │   .npmrc
│   │   netlify.toml
│   │   package-lock.json
│   │   package.json
│   │   README.md
│   │   slides.md
│   │   vercel.json
│   │
│   ├───components
│   │       Counter.vue
│   │
│   ├───layouts
│   │       Standard.vue
│   │
│   ├───pages
│   │       imported-slides.md
│   │
│   ├───public
│   │       img_002_02.png
│   │       img_002_03.png
│   │       img_003_05.png
│   │       img_003_06.png
│   │       img_004_05.png
│   │
│   ├───snippets
│   │       external.ts
│   │
│   └───template
│           multi-agent.md
│
└───src
    │   __init__.py
    │
    ├───extractor
    │       extract_file.py
    │
    ├───generator
    │   │   slide_generator.py
    │   │
    │   └───agents
    │           asset_manager.py
    │           content.py
    │           slidev_renderer.py
    │           template_matcher.py
    │           validator.py
    │           __init__.py
    │
    ├───ingestion
    │       asset_manager.py
    │       context_builder.py
    │       image_filter.py
    │       parser.py
    │       table_converter.py
    │       vision_model.py
    │       __init__.py
    │
    ├───integrations
    │       abstract_classifier.py
    │       genai_image.py
    │       tavily.py
    │       unsplash.py
    │       vision_classifier.py
    │       __init__.py
    │
    ├───models
    │       asset.py
    │       context.py
    │       slide.py
    │       slide_schemas.py
    │       __init__.py
    │
    ├───optimization
    │       lightning_config.py
    │       lightning_integration.py
    │       lightning_manager.py
    │       lightning_setup.py
    │       reward_function.py
    │       __init__.py
    │
    ├───preprocessor
    │       preprocessing_context.py
    │
    ├───utils
    │       config.py
    │       file_utils.py
    │       image_quality.py
    │       latex_processor.py
    │       semantic_match.py
    │       __init__.py
    │
    └───workflow
        │   graph.py
        │   state.py
        │   __init__.py
        │
        └───agents
                asset_manager.py
                coverage_checker.py
                planner.py
                refiner.py
                reviewer.py
                writer.py
                __init__.py