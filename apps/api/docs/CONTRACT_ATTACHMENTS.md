# Contract attachments

Saved contracts support optional PDF, DOCX, PNG and JPEG attachments up to
10 MB each. Use **Attachments** in the client's Contracts tab or the contract
detail page. Uploaded documents also appear in the client's Documents tab.

- `POST /documents/contracts/{contract_id}/attachments`: multipart `file`.
  Requires a non-viewer and a contract in the authenticated tenant. Client,
  tenant and uploader are derived on the server, not accepted from the upload.
- `GET /documents/{document_id}/download`: authenticated, tenant-scoped binary
  download. Files are served as attachments with private/no-store caching.

The existing Document record stores metadata and contract/client associations.
File bytes live under `DOCUMENT_STORAGE_PATH` (default `./uploads` relative to
the API working directory), in tenant-isolated directories with generated
filenames. The original filename is metadata only. Database or audit failure
removes the uploaded file and rolls back the document.

## Deployment requirement

Set `DOCUMENT_STORAGE_PATH` to a persistent, private writable volume and back it
up with the database. All API replicas must share that volume. Do not expose it
as a static/public directory. Ephemeral or read-only serverless filesystems do
not provide durable attachments; those deployments need a separate object-store
adapter before this feature is enabled there.

The Docker Compose API services mount separate named attachment volumes for
development and production. The production image creates the private upload
directory owned by its non-root API user.

Extension and file-header checks are not malware scanning. Download attachments
only from trusted sources. A scanner is not part of this implementation.
