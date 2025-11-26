# yt-dlp Restate service

![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/sagikazarmark/restate-yt-dlp/ci.yaml?style=flat-square)
![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/sagikazarmark/restate-yt-dlp/badge?style=flat-square)

**A Restate service for yt-dlp.**

This service provides a durable, fault-tolerant wrapper around [yt-dlp](https://github.com/yt-dlp/yt-dlp) for downloading videos.
Built on [Restate](https://restate.dev), it ensures reliable video processing with automatic retries, state management, and seamless integration with object storage systems.

## Features

- **Durable Downloads**: Video downloads are handled as durable workflows that can survive failures
- **Object Storage Integration**: Automatically upload downloaded content to object storage systems (currently supports [obstore](https://developmentseed.org/obstore/))
- **Flexible Filtering**: Control which files get uploaded using glob patterns
- **Configurable Options**: Support for all yt-dlp options and parameters
- **Structured Logging**: Comprehensive logging with structured output

## Quickstart

1. **Start the service:**
   ```bash
   # Clone the repository and start dependencies
   docker compose up -d

   # Install dependencies and run the service
   uv sync --extra app
   uv run granian src.main:app --interface restate --port 9080
   ```

2. **Register the service with Restate:**
   ```bash
   # Service URL depends on how you run Restate and the service
   restate deployment register http://host.docker.internal:9080
   ```

3. **Download a video:**
   ```bash
   curl -X POST http://localhost:8080/yt-dlp/download \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
       "output": {
         "ref": "s3://my-bucket/downloads/"
       },
       "options": {
         "format": "best[height<=720]"
       }
     }'
   ```

## Configuration

Configure the service using environment variables:

- `OBSTORE__URL`: Object store URL (e.g., `s3://bucket-name`) (optional)
- `YT_DLP_DEFAULTS`: Default yt-dlp options as JSON
- `SERVICE_NAME`: Service name (default: "yt-dlp")
- `RESTATE_IDENTITY_KEYS`: Restate identity keys (as JSON array)

## Deployment

The recommended deployment method is using containers.

You can either build and run the container yourself or use the pre-built image from GHCR:

```
ghcr.io/sagikazarmark/restate-yt-dlp
```

For production deployments, consider:
- Using persistent volumes for temporary storage
- Setting appropriate resource limits
- Configuring object storage credentials securely
- Setting up monitoring and logging

## Resources

- [Restate Documentation](https://docs.restate.dev)
- [Restate Concepts](https://docs.restate.dev/concepts)
- [Restate Python SDK](https://docs.restate.dev/sdk/python)
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)

## License

The project is licensed under the [MIT License](LICENSE).
