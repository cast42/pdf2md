# Hugging Face Setup

This guide walks through configuring pdf2md to use Hugging Face for OCR inference.

## Choose your backend

You have two options:

- Hosted Inference API (cheaper/free tier): use `HF_MODEL_ID`
- Dedicated Inference Endpoint (GPU): use `HF_ENDPOINT_URL`

Note: the hosted Inference API currently does not list image-to-text providers for most
OCR models. If you see a 404 or “no provider available” error, you will need a dedicated
endpoint.

## Step 1: Create a Hugging Face token

1. Go to <https://huggingface.co/settings/tokens>.
2. Create a new token with **read** access.
3. Copy the token value (do not commit it).

## Step 2A: Hosted Inference API (cheapest option, limited availability)

This path does not require creating an endpoint. You only need a model ID, but it only
works if the model has an available inference provider.

1. Pick a model ID that has an inference provider available on Hugging Face.
   OCR-focused models like `microsoft/trocr-base-printed` and `lightonai/LightOnOCR-2-1B`
   usually require a dedicated endpoint.
2. Set environment variables:

```sh
export HF_TOKEN="your-token"
export HF_MODEL_ID="your-model-id"
```

3. Run:

```sh
just run /path/to/file.pdf
```

Notes:

- Availability and limits depend on your Hugging Face plan.
- If you see rate limits, move to a dedicated endpoint.
- Not every model is available on the hosted Inference API. If you see a
  “No inference provider is available” error, use a dedicated endpoint instead.

## Step 2B: Dedicated Inference Endpoint (GPU)

1. Go to <https://huggingface.co/inference-endpoints>.
2. Create a new endpoint and select the model.
3. For the lowest cost, choose the cheapest GPU available in your region
   (often NVIDIA T4 or L4).
4. If autoscaling to zero is available, enable it to reduce idle cost.
   Otherwise, pause the endpoint when not in use.
5. Copy the endpoint URL and set:

```sh
export HF_TOKEN="your-token"
export HF_ENDPOINT_URL="https://your-endpoint-url"
```

6. Run:

```sh
just run /path/to/file.pdf
```

## Optional settings

```sh
export PDF2MD_BACKEND="endpoint"  # or "local"
export HF_TIMEOUT_S="120"
export HF_RETRIES="4"
```

## Local backend (no Hugging Face)

If you want to run locally:

```sh
uv sync --extra local
export PDF2MD_BACKEND="local"
just run /path/to/file.pdf
```

## Using a .env file

The `justfile` loads `.env`, so you can store your variables there:

```sh
HF_TOKEN=your-token
HF_MODEL_ID=your-model-id
```
