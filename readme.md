tree .
.
├── core
│   ├── blob.py
│   ├── config.py
│   ├── logger.py
│   ├── mongo.py
│   └── redis.py
├── Dockerfile
├── main.py
├── models
│   ├── expense.py
├── python_version.txt
├── requirements.txt
├── routes
│   ├── health.py
│   ├── receipts.py
│   └── users.py
├── scripts
│   └── migrate.py
├── security
│   ├── dependencies.py
│   ├── jwt.py
├── services
│   ├── parser.py
│   ├── receipt_processor.py
│   ├── receipt_uploader.py
│   ├── redis_listener.py
│   └── vision_parser.py
├── tests
│   ├── 001.jpg
│   ├── 001.pdf
│   ├── 002.jpg
│   ├── 003.jpg
│   ├── 005.jpg
│   ├── 006.jpg
│   ├── blob_test.py
│   ├── decode_token.py
│   ├── get-receips.json
│   ├── mock_data.py
│   ├── mock_receipts.json
│   ├── test_app.py
│   ├── test_openai.py
│   └── test_redis.py
└── uploads
    ├── 20250404_072137_d28f6fb9.jpg
    ├── 20250404_085136_ea956d58.jpg
    ├── 20250404_085156_2a3ee37e.jpg
