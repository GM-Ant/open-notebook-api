# Open Notebook API Reference

This comprehensive reference documents all API endpoints available in the Open Notebook REST API, including detailed information about methods, parameters, authentication, and response formats.

## API Base URL

```
https://api.opennotebook.domain/v1
```

## Authentication

The Open Notebook API uses bearer token authentication.

**Header Format:**
```
Authorization: Bearer <your_api_token>
```

> **Note:** The current implementation does not include authentication. In production, implement token-based authentication using FastAPI security utilities.

## API Versioning

API versioning is supported through the `Accept-Version` header.

```
Accept-Version: v1
```

## General Parameters

### Pagination

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number (1-based indexing) |
| `per_page` | integer | Number of items per page (default: 20, max: 100) |
| `cursor` | string | Cursor for cursor-based pagination |

Example:
```
GET /notebooks?page=2&per_page=50
```

### Sorting

Sort results using the `sort_by` parameter:

```
GET /notebooks?sort_by=name:asc
GET /notebooks?sort_by=created:desc
```

Multiple sort fields:
```
GET /notebooks?sort_by=archived:asc,created:desc
```

### Filtering

Filter results using the `filter` parameter with operators:

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Equals | `filter[name]=Research` |
| `!=` | Not equals | `filter[name][ne]=Test` |
| `>` | Greater than | `filter[created][gt]=2023-01-01` |
| `<` | Less than | `filter[created][lt]=2023-01-01` |
| `>=` | Greater than or equal | `filter[created][gte]=2023-01-01` |
| `<=` | Less than or equal | `filter[created][lte]=2023-01-01` |
| `IN` | In a list | `filter[status][in]=active,archived` |
| `BETWEEN` | Between values | `filter[created][between]=2023-01-01,2023-12-31` |

Example:
```
GET /notebooks?filter[archived]=false&filter[created][gt]=2023-01-01
```

### Field Selection

Select specific fields to include in the response:

```
GET /notebooks?fields=id,name,created
```

### Include Relationships

Include related resources:

```
GET /notebooks?expand=sources,notes
```

### Search

Text search with optional fuzzy matching:

```
GET /notebooks?q=machine%20learning
GET /notebooks?q=machne~2  # Fuzzy search with max 2 character difference
```

## Rate Limiting

Rate limit information is included in the response headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1683721584
```

## Conditional Requests

Support for conditional requests to reduce bandwidth and processing:

```
GET /notebooks/nb_123
If-None-Match: "a3f657c8e94a4b9c87f97c3f4c2f2d1a"
```

If the resource hasn't changed:
```
HTTP/1.1 304 Not Modified
ETag: "a3f657c8e94a4b9c87f97c3f4c2f2d1a"
```

## Webhook Configuration

Configure webhooks to receive notifications about events:

| Parameter | Type | Description |
|-----------|------|-------------|
| `events` | array | Array of events to subscribe to |
| `callback_url` | string | URL to receive webhook events |
| `secret` | string | Secret for webhook signature verification |

Example request:
```json
{
  "events": ["notebook.created", "source.added"],
  "callback_url": "https://your-app.com/webhooks/opennotebook",
  "secret": "your_webhook_secret"
}
```

## Batch Operations

Perform multiple operations in a single request:

```json
{
  "batch": [
    {
      "method": "POST",
      "path": "/notebooks",
      "body": {
        "name": "New Notebook 1",
        "description": "Description 1"
      }
    },
    {
      "method": "POST",
      "path": "/notebooks",
      "body": {
        "name": "New Notebook 2",
        "description": "Description 2"
      }
    }
  ]
}
```

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "resource_not_found",
    "message": "Notebook not found: notebook:xyz",
    "details": {
      "resource_type": "notebook",
      "resource_id": "notebook:xyz"
    }
  }
}
```

Common HTTP status codes:

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |

---

## Notebooks API

### List Notebooks

Retrieves a list of notebooks with pagination and filtering.

**Endpoint:** `GET /notebooks`  
**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `include_archived` | boolean | No | Include archived notebooks (default: false) |
| `page` | integer | No | Page number (default: 1) |
| `per_page` | integer | No | Items per page (default: 20, max: 100) |
| `sort_by` | string | No | Sorting order (default: "created:desc") |
| `q` | string | No | Text search query |
| `fields` | string | No | Comma-separated list of fields to include |
| `expand` | string | No | Related resources to include |
| `filter[name]` | string | No | Filter by name |
| `filter[archived]` | boolean | No | Filter by archived status |
| `filter[created][gt]` | string | No | Filter by creation date (greater than) |
| `filter[created][lt]` | string | No | Filter by creation date (less than) |

**Example Request:**
```
GET /notebooks?include_archived=true&sort_by=created:desc&per_page=50
```

**Example Response:**
```json
{
  "data": [
    {
      "id": "notebook:123",
      "name": "Machine Learning Research",
      "description": "Notes on ML research papers",
      "created": "2023-05-01T10:00:00Z",
      "updated": "2023-05-05T14:30:00Z",
      "archived": false,
      "sources_count": 12,
      "notes_count": 5
    },
    {
      "id": "notebook:124",
      "name": "Project Ideas",
      "description": "Collection of project ideas",
      "created": "2023-04-20T09:15:00Z",
      "updated": "2023-04-22T16:45:00Z",
      "archived": false,
      "sources_count": 3,
      "notes_count": 8
    }
  ],
  "meta": {
    "total": 45,
    "page": 1,
    "per_page": 50,
    "pages": 1
  },
  "links": {
    "self": "/notebooks?include_archived=true&sort_by=created:desc&per_page=50&page=1",
    "first": "/notebooks?include_archived=true&sort_by=created:desc&per_page=50&page=1",
    "last": "/notebooks?include_archived=true&sort_by=created:desc&per_page=50&page=1"
  }
}
```

### Get Notebook

Retrieves a specific notebook by ID.

**Endpoint:** `GET /notebooks/{notebook_id}`  
**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `notebook_id` | string | Yes | Notebook ID |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `fields` | string | No | Comma-separated list of fields to include |
| `expand` | string | No | Related resources to include (e.g., "sources,notes") |

**Example Request:**
```
GET /notebooks/notebook:123?expand=sources,notes
```

**Example Response:**
```json
{
  "data": {
    "id": "notebook:123",
    "name": "Machine Learning Research",
    "description": "Notes on ML research papers",
    "created": "2023-05-01T10:00:00Z",
    "updated": "2023-05-05T14:30:00Z",
    "archived": false,
    "sources_count": 12,
    "notes_count": 5,
    "sources": [
      {
        "id": "src:456",
        "title": "Introduction to Neural Networks",
        "type": "text",
        "created": "2023-05-01T10:05:00Z"
      }
    ],
    "notes": [
      {
        "id": "note:789",
        "title": "Key Neural Network Concepts",
        "type": "human",
        "created": "2023-05-02T14:20:00Z"
      }
    ]
  }
}
```

### Create Notebook

Creates a new notebook.

**Endpoint:** `POST /notebooks`  
**Authentication:** Required  
**Content-Type:** `application/json`

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Name of the notebook (1-100 characters) |
| `description` | string | No | Description of the notebook |

**Example Request:**
```json
{
  "name": "AI Research",
  "description": "Notes on artificial intelligence papers and concepts"
}
```

**Example Response:**
```json
{
  "data": {
    "id": "notebook:125",
    "name": "AI Research",
    "description": "Notes on artificial intelligence papers and concepts",
    "created": "2023-05-09T08:12:34Z",
    "updated": "2023-05-09T08:12:34Z",
    "archived": false,
    "sources_count": 0,
    "notes_count": 0
  }
}
```

### Update Notebook

Updates an existing notebook.

**Endpoint:** `PATCH /notebooks/{notebook_id}`  
**Authentication:** Required  
**Content-Type:** `application/json`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `notebook_id` | string | Yes | Notebook ID |

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | No | Name of the notebook (1-100 characters) |
| `description` | string | No | Description of the notebook |

**Example Request:**
```json
{
  "description": "Updated description for AI research notebook"
}
```

**Example Response:**
```json
{
  "data": {
    "id": "notebook:125",
    "name": "AI Research",
    "description": "Updated description for AI research notebook",
    "created": "2023-05-09T08:12:34Z",
    "updated": "2023-05-09T09:30:45Z",
    "archived": false,
    "sources_count": 0,
    "notes_count": 0
  }
}
```

### Archive Notebook

Archives a notebook.

**Endpoint:** `POST /notebooks/{notebook_id}/archive`  
**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `notebook_id` | string | Yes | Notebook ID |

**Example Request:**
```
POST /notebooks/notebook:125/archive
```

**Example Response:**
```json
{
  "data": {
    "id": "notebook:125",
    "name": "AI Research",
    "archived": true,
    "updated": "2023-05-09T10:15:22Z"
  }
}
```

### Unarchive Notebook

Unarchives a notebook.

**Endpoint:** `POST /notebooks/{notebook_id}/unarchive`  
**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `notebook_id` | string | Yes | Notebook ID |

**Example Request:**
```
POST /notebooks/notebook:125/unarchive
```

**Example Response:**
```json
{
  "data": {
    "id": "notebook:125",
    "name": "AI Research",
    "archived": false,
    "updated": "2023-05-09T10:20:15Z"
  }
}
```

### Delete Notebook

Deletes a notebook.

**Endpoint:** `DELETE /notebooks/{notebook_id}`  
**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `notebook_id` | string | Yes | Notebook ID |

**Example Request:**
```
DELETE /notebooks/notebook:125
```

**Example Response:**
```
HTTP/1.1 204 No Content
```

---

## Sources API

### List Sources

Retrieves a list of sources in a notebook.

**Endpoint:** `GET /notebooks/{notebook_id}/sources`  
**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `notebook_id` | string | Yes | Notebook ID |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `per_page` | integer | No | Items per page (default: 20, max: 100) |
| `sort_by` | string | No | Sorting order (default: "created:desc") |
| `q` | string | No | Text search query |
| `fields` | string | No | Comma-separated list of fields to include |
| `type` | string | No | Filter by source type (text, url, file) |
| `filter[title]` | string | No | Filter by title |
| `filter[created][gt]` | string | No | Filter by creation date (greater than) |
| `filter[embedded]` | boolean | No | Filter by embedding status |

**Example Request:**
```
GET /notebooks/notebook:123/sources?sort_by=created:desc&type=text
```

**Example Response:**
```json
{
  "data": [
    {
      "id": "src:456",
      "title": "Introduction to Neural Networks",
      "type": "text",
      "created": "2023-05-01T10:05:00Z",
      "updated": "2023-05-01T10:05:00Z",
      "embedded_chunks": 5,
      "insights_count": 2,
      "notebook_id": "notebook:123"
    },
    {
      "id": "src:457",
      "title": "Deep Learning Fundamentals",
      "type": "text",
      "created": "2023-04-28T15:30:00Z",
      "updated": "2023-04-28T15:30:00Z",
      "embedded_chunks": 8,
      "insights_count": 3,
      "notebook_id": "notebook:123"
    }
  ],
  "meta": {
    "total": 8,
    "page": 1,
    "per_page": 20,
    "pages": 1
  },
  "links": {
    "self": "/notebooks/notebook:123/sources?sort_by=created:desc&type=text&page=1",
    "first": "/notebooks/notebook:123/sources?sort_by=created:desc&type=text&page=1",
    "last": "/notebooks/notebook:123/sources?sort_by=created:desc&type=text&page=1"
  }
}
```

### Get Source

Retrieves a specific source by ID.

**Endpoint:** `GET /sources/{source_id}`  
**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_id` | string | Yes | Source ID |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `full_text` | boolean | No | Include full text of the source (default: false) |
| `show_insights` | boolean | No | Include insights for the source (default: false) |
| `fields` | string | No | Comma-separated list of fields to include |

**Example Request:**
```
GET /sources/src:456?full_text=true&show_insights=true
```

**Example Response:**
```json
{
  "data": {
    "id": "src:456",
    "title": "Introduction to Neural Networks",
    "type": "text",
    "created": "2023-05-01T10:05:00Z",
    "updated": "2023-05-01T10:05:00Z",
    "notebook_id": "notebook:123",
    "embedded_chunks": 5,
    "insights_count": 2,
    "content": "Neural networks are computational models inspired by the human brain...",
    "insights": [
      {
        "id": "ins:1",
        "content": "Neural networks consist of layers of interconnected nodes.",
        "transformation_id": "trans:1",
        "created": "2023-05-01T10:10:00Z"
      },
      {
        "id": "ins:2",
        "content": "The basic unit of a neural network is called a perceptron.",
        "transformation_id": "trans:1",
        "created": "2023-05-01T10:10:00Z"
      }
    ]
  }
}
```

### Add Text Source

Adds a text source to a notebook.

**Endpoint:** `POST /notebooks/{notebook_id}/sources/text`  
**Authentication:** Required  
**Content-Type:** `application/json`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `notebook_id` | string | Yes | Notebook ID |

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Title of the source (1-200 characters) |
| `content` | string | Yes | Content of the source |
| `embed` | boolean | No | Generate embeddings for the source (default: false) |
| `transform` | boolean | No | Apply standard transformations (default: false) |
| `apply_transformations` | array | No | Array of transformation IDs to apply |

**Example Request:**
```json
{
  "title": "Introduction to Neural Networks",
  "content": "Neural networks are computational models inspired by the human brain...",
  "embed": true,
  "transform": true
}
```

**Example Response:**
```json
{
  "data": {
    "id": "src:458",
    "title": "Introduction to Neural Networks",
    "type": "text",
    "created": "2023-05-09T11:05:22Z",
    "updated": "2023-05-09T11:05:22Z",
    "notebook_id": "notebook:123",
    "embedding_status": "pending",
    "transformation_status": "pending"
  }
}
```

### Add URL Source

Adds a URL source to a notebook.

**Endpoint:** `POST /notebooks/{notebook_id}/sources/url`  
**Authentication:** Required  
**Content-Type:** `application/json`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `notebook_id` | string | Yes | Notebook ID |

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | Yes | URL of the source (valid URL format) |
| `embed` | boolean | No | Generate embeddings for the source (default: false) |
| `transform` | boolean | No | Apply standard transformations (default: false) |
| `apply_transformations` | array | No | Array of transformation IDs to apply |

**Example Request:**
```json
{
  "url": "https://example.com/article-about-neural-networks",
  "embed": true,
  "transform": true
}
```

**Example Response:**
```json
{
  "data": {
    "id": "src:459",
    "title": "https://example.com/article-about-neural-networks",
    "type": "url",
    "created": "2023-05-09T11:15:30Z",
    "updated": "2023-05-09T11:15:30Z",
    "notebook_id": "notebook:123",
    "url": "https://example.com/article-about-neural-networks",
    "embedding_status": "pending",
    "transformation_status": "pending"
  }
}
```

### Embed Source

Generates embeddings for a source.

**Endpoint:** `POST /sources/{source_id}/embed`  
**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_id` | string | Yes | Source ID |

**Example Request:**
```
POST /sources/src:458/embed
```

**Example Response:**
```json
{
  "data": {
    "id": "src:458",
    "embedding_status": "processing",
    "expected_chunks": 10
  }
}
```

### Apply Transformation

Applies transformations to a source.

**Endpoint:** `POST /sources/{source_id}/transform`  
**Authentication:** Required  
**Content-Type:** `application/json`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_id` | string | Yes | Source ID |

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transformation_id` | string | No | ID of a specific transformation to apply |
| `transform` | boolean | No | Apply standard transformations (default: false) |

**Example Request:**
```json
{
  "transformation_id": "trans:1"
}
```

**Example Response:**
```json
{
  "data": {
    "id": "src:458",
    "transformation_status": "processing",
    "transformation_id": "trans:1"
  }
}
```

**Alternative Request (standard transformations):**
```json
{
  "transform": true
}
```

### Delete Source

Deletes a source.

**Endpoint:** `DELETE /sources/{source_id}`  
**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_id` | string | Yes | Source ID |

**Example Request:**
```
DELETE /sources/src:458
```

**Example Response:**
```
HTTP/1.1 204 No Content
```

---

## Notes API

### List Notes

Retrieves a list of notes in a notebook.

**Endpoint:** `GET /notebooks/{notebook_id}/notes`  
**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `notebook_id` | string | Yes | Notebook ID |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `per_page` | integer | No | Items per page (default: 20, max: 100) |
| `sort_by` | string | No | Sorting order (default: "created:desc") |
| `q` | string | No | Text search query |
| `type` | string | No | Filter by note type (human, ai) |
| `filter[title]` | string | No | Filter by title |
| `filter[created][gt]` | string | No | Filter by creation date (greater than) |

**Example Request:**
```
GET /notebooks/notebook:123/notes?type=human&sort_by=created:desc
```

**Example Response:**
```json
{
  "data": [
    {
      "id": "note:789",
      "title": "Key Neural Network Concepts",
      "type": "human",
      "created": "2023-05-02T14:20:00Z",
      "updated": "2023-05-02T14:20:00Z",
      "notebook_id": "notebook:123"
    },
    {
      "id": "note:790",
      "title": "Questions About Backpropagation",
      "type": "human",
      "created": "2023-05-01T16:45:00Z",
      "updated": "2023-05-01T16:45:00Z",
      "notebook_id": "notebook:123"
    }
  ],
  "meta": {
    "total": 3,
    "page": 1,
    "per_page": 20,
    "pages": 1
  },
  "links": {
    "self": "/notebooks/notebook:123/notes?type=human&sort_by=created:desc&page=1",
    "first": "/notebooks/notebook:123/notes?type=human&sort_by=created:desc&page=1",
    "last": "/notebooks/notebook:123/notes?type=human&sort_by=created:desc&page=1"
  }
}
```

### Get Note

Retrieves a specific note by ID.

**Endpoint:** `GET /notes/{note_id}`  
**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `note_id` | string | Yes | Note ID |

**Example Request:**
```
GET /notes/note:789
```

**Example Response:**
```json
{
  "data": {
    "id": "note:789",
    "title": "Key Neural Network Concepts",
    "content": "1. Neurons are the basic computational units...",
    "type": "human",
    "created": "2023-05-02T14:20:00Z",
    "updated": "2023-05-02T14:20:00Z",
    "notebook_id": "notebook:123"
  }
}
```

### Create Note

Creates a new note in a notebook.

**Endpoint:** `POST /notebooks/{notebook_id}/notes`  
**Authentication:** Required  
**Content-Type:** `application/json`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `notebook_id` | string | Yes | Notebook ID |

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Title of the note (1-200 characters) |
| `content` | string | Yes | Content of the note |
| `type` | string | No | Type of the note (human, ai) (default: "human") |

**Example Request:**
```json
{
  "title": "Activation Functions",
  "content": "Common activation functions include ReLU, Sigmoid, and Tanh...",
  "type": "human"
}
```

**Example Response:**
```json
{
  "data": {
    "id": "note:791",
    "title": "Activation Functions",
    "content": "Common activation functions include ReLU, Sigmoid, and Tanh...",
    "type": "human",
    "created": "2023-05-09T12:15:45Z",
    "updated": "2023-05-09T12:15:45Z",
    "notebook_id": "notebook:123"
  }
}
```

### Update Note

Updates an existing note.

**Endpoint:** `PATCH /notes/{note_id}`  
**Authentication:** Required  
**Content-Type:** `application/json`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `note_id` | string | Yes | Note ID |

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | Title of the note (1-200 characters) |
| `content` | string | No | Content of the note |

**Example Request:**
```json
{
  "title": "Updated: Activation Functions in Neural Networks",
  "content": "Updated content about activation functions..."
}
```

**Example Response:**
```json
{
  "data": {
    "id": "note:791",
    "title": "Updated: Activation Functions in Neural Networks",
    "content": "Updated content about activation functions...",
    "type": "human",
    "created": "2023-05-09T12:15:45Z",
    "updated": "2023-05-09T12:30:10Z",
    "notebook_id": "notebook:123"
  }
}
```

### Convert Source Insight to Note

Converts a source insight to a note.

**Endpoint:** `POST /notebooks/{notebook_id}/notes/from-insight/{source_insight_id}`  
**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `notebook_id` | string | Yes | Notebook ID |
| `source_insight_id` | string | Yes | Source Insight ID |

**Example Request:**
```
POST /notebooks/notebook:123/notes/from-insight/ins:1
```

**Example Response:**
```json
{
  "data": {
    "id": "note:792",
    "title": "Note from Insight ins:1",
    "content": "Neural networks consist of layers of interconnected nodes.",
    "type": "ai",
    "created": "2023-05-09T13:05:30Z",
    "updated": "2023-05-09T13:05:30Z",
    "notebook_id": "notebook:123",
    "source_insight_id": "ins:1"
  }
}
```

### Delete Note

Deletes a note.

**Endpoint:** `DELETE /notes/{note_id}`  
**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `note_id` | string | Yes | Note ID |

**Example Request:**
```
DELETE /notes/note:791
```

**Example Response:**
```
HTTP/1.1 204 No Content
```

---

## Transformation API

### List Transformations

Retrieves a list of available transformations.

**Endpoint:** `GET /transformations`  
**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `per_page` | integer | No | Items per page (default: 20, max: 100) |
| `sort_by` | string | No | Sorting order (default: "name:asc") |
| `apply_default` | boolean | No | Filter by default application status |

**Example Request:**
```
GET /transformations?apply_default=true
```

**Example Response:**
```json
{
  "data": [
    {
      "id": "trans:1",
      "name": "Summary",
      "short_code": "sum",
      "apply_default": true,
      "created": "2023-01-01T00:00:00Z"
    },
    {
      "id": "trans:2",
      "name": "Key Points",
      "short_code": "key",
      "apply_default": true,
      "created": "2023-01-01T00:00:00Z"
    }
  ],
  "meta": {
    "total": 2,
    "page": 1,
    "per_page": 20,
    "pages": 1
  }
}
```

### Get Transformation

Retrieves a specific transformation by ID.

**Endpoint:** `GET /transformations/{transformation_id}`  
**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `transformation_id` | string | Yes | Transformation ID |

**Example Request:**
```
GET /transformations/trans:1
```

**Example Response:**
```json
{
  "data": {
    "id": "trans:1",
    "name": "Summary",
    "short_code": "sum",
    "description": "Creates a summary of the source content.",
    "prompt_template": "Summarize the following text:\n\n{{text}}",
    "apply_default": true,
    "created": "2023-01-01T00:00:00Z",
    "updated": "2023-01-01T00:00:00Z"
  }
}
```

### Create Transformation

Creates a new transformation.

**Endpoint:** `POST /transformations`  
**Authentication:** Required  
**Content-Type:** `application/json`

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Name of the transformation (1-100 characters) |
| `short_code` | string | Yes | Short code for the transformation (2-10 characters) |
| `description` | string | Yes | Description of the transformation |
| `prompt_template` | string | Yes | Prompt template for the transformation |
| `apply_default` | boolean | No | Apply this transformation by default (default: false) |

**Example Request:**
```json
{
  "name": "Question Generator",
  "short_code": "qgen",
  "description": "Generates questions based on the content",
  "prompt_template": "Generate 5 insightful questions based on this text:\n\n{{text}}",
  "apply_default": false
}
```

**Example Response:**
```json
{
  "data": {
    "id": "trans:3",
    "name": "Question Generator",
    "short_code": "qgen",
    "description": "Generates questions based on the content",
    "prompt_template": "Generate 5 insightful questions based on this text:\n\n{{text}}",
    "apply_default": false,
    "created": "2023-05-09T14:20:45Z",
    "updated": "2023-05-09T14:20:45Z"
  }
}
```

### Update Transformation

Updates an existing transformation.

**Endpoint:** `PATCH /transformations/{transformation_id}`  
**Authentication:** Required  
**Content-Type:** `application/json`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `transformation_id` | string | Yes | Transformation ID |

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | No | Name of the transformation (1-100 characters) |
| `description` | string | No | Description of the transformation |
| `prompt_template` | string | No | Prompt template for the transformation |
| `apply_default` | boolean | No | Apply this transformation by default |

**Example Request:**
```json
{
  "description": "Updated description for question generator",
  "apply_default": true
}
```

**Example Response:**
```json
{
  "data": {
    "id": "trans:3",
    "name": "Question Generator",
    "short_code": "qgen",
    "description": "Updated description for question generator",
    "prompt_template": "Generate 5 insightful questions based on this text:\n\n{{text}}",
    "apply_default": true,
    "created": "2023-05-09T14:20:45Z",
    "updated": "2023-05-09T14:35:20Z"
  }
}
```

### Delete Transformation

Deletes a transformation.

**Endpoint:** `DELETE /transformations/{transformation_id}`  
**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `transformation_id` | string | Yes | Transformation ID |

**Example Request:**
```
DELETE /transformations/trans:3
```

**Example Response:**
```
HTTP/1.1 204 No Content
```

---

## Chat API

### List Chat Sessions

Retrieves a list of chat sessions for a notebook.

**Endpoint:** `GET /notebooks/{notebook_id}/chat-sessions`  
**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `notebook_id` | string | Yes | Notebook ID |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `per_page` | integer | No | Items per page (default: 20, max: 100) |
| `sort_by` | string | No | Sorting order (default: "created:desc") |

**Example Request:**
```
GET /notebooks/notebook:123/chat-sessions
```

**Example Response:**
```json
{
  "data": [
    {
      "id": "chat:1",
      "title": "Research Discussion",
      "created": "2023-05-05T10:00:00Z",
      "updated": "2023-05-05T11:30:00Z",
      "notebook_id": "notebook:123",
      "messages_count": 12
    },
    {
      "id": "chat:2",
      "title": "Project Planning",
      "created": "2023-05-03T14:20:00Z",
      "updated": "2023-05-03T15:45:00Z",
      "notebook_id": "notebook:123",
      "messages_count": 8
    }
  ],
  "meta": {
    "total": 2,
    "page": 1,
    "per_page": 20,
    "pages": 1
  }
}
```

### Get Chat Session

Retrieves a specific chat session with messages.

**Endpoint:** `GET /chat-sessions/{chat_session_id}`  
**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `chat_session_id` | string | Yes | Chat Session ID |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `include_messages` | boolean | No | Include messages in the response (default: true) |
| `page` | integer | No | Page for messages (default: 1) |
| `per_page` | integer | No | Messages per page (default: 50, max: 100) |

**Example Request:**
```
GET /chat-sessions/chat:1?include_messages=true&per_page=10
```

**Example Response:**
```json
{
  "data": {
    "id": "chat:1",
    "title": "Research Discussion",
    "created": "2023-05-05T10:00:00Z",
    "updated": "2023-05-05T11:30:00Z",
    "notebook_id": "notebook:123",
    "messages_count": 12,
    "messages": [
      {
        "id": "msg:1",
        "content": "What are the key concepts in neural networks?",
        "role": "user",
        "created": "2023-05-05T10:00:00Z"
      },
      {
        "id": "msg:2",
        "content": "Neural networks consist of layers of interconnected nodes...",
        "role": "assistant",
        "created": "2023-05-05T10:00:10Z",
        "referenced_sources": ["src:456"]
      }
    ]
  },
  "meta": {
    "messages_total": 12,
    "messages_page": 1,
    "messages_per_page": 10,
    "messages_pages": 2
  },
  "links": {
    "messages_next": "/chat-sessions/chat:1/messages?page=2&per_page=10"
  }
}
```

### Create Chat Session

Creates a new chat session for a notebook.

**Endpoint:** `POST /notebooks/{notebook_id}/chat-sessions`  
**Authentication:** Required  
**Content-Type:** `application/json`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `notebook_id` | string | Yes | Notebook ID |

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Title of the chat session (1-100 characters) |

**Example Request:**
```json
{
  "title": "Deep Learning Discussion"
}
```

**Example Response:**
```json
{
  "data": {
    "id": "chat:3",
    "title": "Deep Learning Discussion",
    "created": "2023-05-09T15:05:30Z",
    "updated": "2023-05-09T15:05:30Z",
    "notebook_id": "notebook:123",
    "messages_count": 0
  }
}
```

### Add Message to Chat

Adds a new message to a chat session.

**Endpoint:** `POST /chat-sessions/{chat_session_id}/messages`  
**Authentication:** Required  
**Content-Type:** `application/json`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `chat_session_id` | string | Yes | Chat Session ID |

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | string | Yes | Content of the message |
| `role` | string | Yes | Role (user, assistant, system) |
| `referenced_sources` | array | No | Source IDs referenced in the message |

**Example Request:**
```json
{
  "content": "Can you explain how Convolutional Neural Networks work?",
  "role": "user"
}
```

**Example Response:**
```json
{
  "data": {
    "id": "msg:13",
    "content": "Can you explain how Convolutional Neural Networks work?",
    "role": "user",
    "created": "2023-05-09T15:10:45Z",
    "chat_session_id": "chat:3"
  }
}
```

### Delete Chat Session

Deletes a chat session.

**Endpoint:** `DELETE /chat-sessions/{chat_session_id}`  
**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `chat_session_id` | string | Yes | Chat Session ID |

**Example Request:**
```
DELETE /chat-sessions/chat:3
```

**Example Response:**
```
HTTP/1.1 204 No Content
```

---

## Search API

### Text Search

Performs a text-based search across sources and notes.

**Endpoint:** `GET /search/text`  
**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Search query |
| `notebook_id` | string | No | Limit search to a specific notebook |
| `include_sources` | boolean | No | Include sources in search results (default: true) |
| `include_notes` | boolean | No | Include notes in search results (default: true) |
| `results` | integer | No | Number of results to return (default: 10, max: 50) |
| `page` | integer | No | Page number (default: 1) |

**Example Request:**
```
GET /search/text?q=neural%20networks&results=5&include_sources=true&include_notes=true
```

**Example Response:**
```json
{
  "data": [
    {
      "id": "src:456",
      "type": "source",
      "title": "Introduction to Neural Networks",
      "score": 0.95,
      "notebook_id": "notebook:123",
      "created": "2023-05-01T10:05:00Z",
      "snippet": "...neural networks are computational models inspired by the human brain..."
    },
    {
      "id": "note:789",
      "type": "note",
      "title": "Key Neural Network Concepts",
      "score": 0.85,
      "notebook_id": "notebook:123",
      "created": "2023-05-02T14:20:00Z",
      "snippet": "...key components of neural networks include neurons, layers, and activation functions..."
    }
  ],
  "meta": {
    "total": 12,
    "page": 1,
    "results_per_page": 5,
    "pages": 3,
    "query": "neural networks"
  },
  "links": {
    "self": "/search/text?q=neural%20networks&results=5&page=1",
    "next": "/search/text?q=neural%20networks&results=5&page=2"
  }
}
```

### Vector Search

Performs a semantic (vector) search across embedded sources and notes.

**Endpoint:** `GET /search/vector`  
**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Search query |
| `notebook_id` | string | No | Limit search to a specific notebook |
| `include_sources` | boolean | No | Include sources in search results (default: true) |
| `include_notes` | boolean | No | Include notes in search results (default: true) |
| `results` | integer | No | Number of results to return (default: 5, max: 50) |
| `min_score` | float | No | Minimum similarity score (0-1) (default: 0.2) |

**Example Request:**
```
GET /search/vector?q=How%20do%20neural%20networks%20learn&results=3&min_score=0.5
```

**Example Response:**
```json
{
  "data": [
    {
      "id": "src:456",
      "type": "source",
      "title": "Introduction to Neural Networks",
      "score": 0.85,
      "notebook_id": "notebook:123",
      "created": "2023-05-01T10:05:00Z",
      "content_snippet": "...neural networks learn through a process called backpropagation..."
    },
    {
      "id": "src:457",
      "type": "source",
      "title": "Deep Learning Fundamentals",
      "score": 0.78,
      "notebook_id": "notebook:123",
      "created": "2023-04-28T15:30:00Z",
      "content_snippet": "...the learning process involves adjusting weights based on error gradients..."
    },
    {
      "id": "note:789",
      "type": "note",
      "title": "Key Neural Network Concepts",
      "score": 0.72,
      "notebook_id": "notebook:123",
      "created": "2023-05-02T14:20:00Z",
      "content_snippet": "...learning in neural networks happens through optimization algorithms like gradient descent..."
    }
  ],
  "meta": {
    "total_above_threshold": 8,
    "query": "How do neural networks learn",
    "min_score": 0.5
  }
}
```

---

## Podcast API

### List Podcast Templates

Retrieves a list of available podcast templates.

**Endpoint:** `GET /podcast-templates`  
**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `per_page` | integer | No | Items per page (default: 20, max: 100) |

**Example Request:**
```
GET /podcast-templates
```

**Example Response:**
```json
{
  "data": [
    {
      "id": "ptmpl:1",
      "name": "Default Template",
      "created": "2023-01-01T00:00:00Z"
    },
    {
      "id": "ptmpl:2",
      "name": "Interview Style",
      "created": "2023-01-01T00:00:00Z"
    }
  ],
  "meta": {
    "total": 2,
    "page": 1,
    "per_page": 20,
    "pages": 1
  }
}
```

### Get Podcast Template

Retrieves a specific podcast template by ID.

**Endpoint:** `GET /podcast-templates/{template_id}`  
**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `template_id` | string | Yes | Podcast Template ID |

**Example Request:**
```
GET /podcast-templates/ptmpl:1
```

**Example Response:**
```json
{
  "data": {
    "id": "ptmpl:1",
    "name": "Default Template",
    "description": "A default podcast template for general content.",
    "created": "2023-01-01T00:00:00Z",
    "updated": "2023-01-01T00:00:00Z",
    "prompt_template": "Create a podcast script based on the following content: {{content}}",
    "voice_options": ["neutral", "friendly"]
  }
}
```

### List Podcast Episodes

Retrieves a list of podcast episodes.

**Endpoint:** `GET /podcast-episodes`  
**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `per_page` | integer | No | Items per page (default: 20, max: 100) |
| `sort_by` | string | No | Sorting order (default: "created:desc") |
| `notebook_id` | string | No | Filter by notebook ID |
| `status` | string | No | Filter by status (pending, processing, completed, failed) |

**Example Request:**
```
GET /podcast-episodes?sort_by=created:desc&status=completed
```

**Example Response:**
```json
{
  "data": [
    {
      "id": "ep:1",
      "name": "Introduction to Machine Learning",
      "status": "completed",
      "created": "2023-05-05T10:00:00Z",
      "completed": "2023-05-05T10:15:30Z",
      "notebook_id": "notebook:123",
      "template_id": "ptmpl:1",
      "audio_url": "/api/podcast-episodes/ep:1/audio",
      "duration_seconds": 420
    },
    {
      "id": "ep:2",
      "name": "Deep Learning Basics",
      "status": "completed",
      "created": "2023-05-03T14:00:00Z",
      "completed": "2023-05-03T14:22:15Z",
      "notebook_id": "notebook:123",
      "template_id": "ptmpl:1",
      "audio_url": "/api/podcast-episodes/ep:2/audio",
      "duration_seconds": 645
    }
  ],
  "meta": {
    "total": 2,
    "page": 1,
    "per_page": 20,
    "pages": 1
  }
}
```

### Get Podcast Episode

Retrieves a specific podcast episode by ID.

**Endpoint:** `GET /podcast-episodes/{episode_id}`  
**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `episode_id` | string | Yes | Podcast Episode ID |

**Example Request:**
```
GET /podcast-episodes/ep:1
```

**Example Response:**
```json
{
  "data": {
    "id": "ep:1",
    "name": "Introduction to Machine Learning",
    "status": "completed",
    "created": "2023-05-05T10:00:00Z",
    "updated": "2023-05-05T10:15:30Z",
    "completed": "2023-05-05T10:15:30Z",
    "notebook_id": "notebook:123",
    "template_id": "ptmpl:1",
    "audio_url": "/api/podcast-episodes/ep:1/audio",
    "transcript_url": "/api/podcast-episodes/ep:1/transcript",
    "duration_seconds": 420,
    "voices": ["neutral"],
    "script_summary": "An introduction to machine learning concepts and techniques..."
  }
}
```

### Generate Podcast

Generates a podcast from a notebook.

**Endpoint:** `POST /notebooks/{notebook_id}/podcast-episodes`  
**Authentication:** Required  
**Content-Type:** `application/json`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `notebook_id` | string | Yes | Notebook ID |

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `template_id` | string | Yes | ID of the podcast template |
| `episode_name` | string | Yes | Name of the podcast episode (1-200 characters) |
| `instructions` | string | No | Additional instructions for podcast generation |
| `longform` | boolean | No | Generate a longer podcast (default: false) |
| `voices` | array | No | Array of voice IDs to use (defaults to template voices) |

**Example Request:**
```json
{
  "template_id": "ptmpl:1",
  "episode_name": "Machine Learning Basics",
  "instructions": "Focus on beginner concepts and include practical examples",
  "longform": true,
  "voices": ["friendly"]
}
```

**Example Response:**
```json
{
  "data": {
    "id": "ep:3",
    "name": "Machine Learning Basics",
    "status": "processing",
    "created": "2023-05-09T16:10:30Z",
    "notebook_id": "notebook:123",
    "template_id": "ptmpl:1",
    "longform": true,
    "estimated_completion_time": "2023-05-09T16:25:00Z"
  }
}
```

### Get Podcast Audio

Retrieves the audio file for a podcast episode.

**Endpoint:** `GET /podcast-episodes/{episode_id}/audio`  
**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `episode_id` | string | Yes | Podcast Episode ID |

**Example Request:**
```
GET /podcast-episodes/ep:1/audio
```

**Response:**
Audio file (MP3) with appropriate content-type headers.

### Get Podcast Transcript

Retrieves the transcript for a podcast episode.

**Endpoint:** `GET /podcast-episodes/{episode_id}/transcript`  
**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `episode_id` | string | Yes | Podcast Episode ID |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `format` | string | No | Transcript format (text, json, srt, vtt) (default: "text") |

**Example Request:**
```
GET /podcast-episodes/ep:1/transcript?format=json
```

**Example Response (format=json):**
```json
{
  "data": {
    "episode_id": "ep:1",
    "name": "Introduction to Machine Learning",
    "transcript": [
      {
        "start": 0.0,
        "end": 3.5,
        "text": "Welcome to this podcast on machine learning."
      },
      {
        "start": 3.7,
        "end": 10.2,
        "text": "Today we'll be covering the basic concepts and applications of machine learning in everyday life."
      }
    ]
  }
}
```

### Delete Podcast Episode

Deletes a podcast episode.

**Endpoint:** `DELETE /podcast-episodes/{episode_id}`  
**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `episode_id` | string | Yes | Podcast Episode ID |

**Example Request:**
```
DELETE /podcast-episodes/ep:3
```

**Example Response:**
```
HTTP/1.1 204 No Content
```
