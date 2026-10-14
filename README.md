# MedVision AI

MedVision AI is a student research prototype for bone-fracture segmentation and severity heuristics from JPG/PNG X-ray images. It includes a PyTorch backend and a React/Vite frontend for local demonstrations.

## Important Safety Notice

**This project is not for clinical use.** It has not been clinically validated, approved by a medical regulator, or tested for use in diagnosis or treatment. Results are experimental and require qualified human review. Do not upload identifiable patient data.

## Dataset

The training and demonstration pipeline can use **FracAtlas**, a dataset for fracture classification, localization, and segmentation of musculoskeletal radiographs.

- Project link: <https://github.com/XLR8-07/FracAtlas>
- Citation: Abedeen, I., Rahman, M.A., Prottyasha, F.Z. et al. *FracAtlas: A Dataset for Fracture Classification, Localization and Segmentation of Musculoskeletal Radiographs.* Scientific Data 10, 521 (2023). [DOI](https://doi.org/10.1038/s41597-023-02432-4).
- Dataset **CC BY 4.0**, verified from [FracAtlas v6 provider metadata](https://api.figshare.com/v2/articles/22363012/versions/6). Attribute the dataset/paper, link the license and identify changes. The preserved archive matches v6; see [data audit](experiments/phase3_review/DATASET_AUDIT.md).

The `FracAtlas.zip` archive is intentionally excluded from version control. Obtain it only from an authorized source, confirm its terms, and place it at the project root if local training or dataset diagnostics are required.

## Model

The trained checkpoint `best_model.pt` is intentionally excluded from version control because it is a large binary artifact. Obtain the checkpoint from the project owner or an approved model-storage location, verify its provenance, and place it at the project root. Do not redistribute it until its training-data and model-license permissions are confirmed.

## Setup

For the verified local installation, run `./Start-Demo.ps1` and open http://localhost:8000/login. See [DEMO.md](DEMO.md) for setup, safe experiment commands and current limitations. Original model/data hashes and measured results are indexed in [EXPERIMENT_REGISTRY.md](EXPERIMENT_REGISTRY.md).

1. Prepare the separate patched CPU serving environment using `requirements-demo.txt` and the commands in [DEMO.md](DEMO.md). Keep the active training environment unchanged.
2. Install the frontend dependencies with `npm ci`.
3. Build with `VITE_API_BASE_URL=/` and `VITE_USE_MOCKS=false` as shown in DEMO.md. Production builds always disable mocks.
4. Run `./Start-Demo.ps1`; it binds the backend and built frontend to loopback port 8000.
5. Sign in using the account and password-file instructions printed by the launcher. The password is generated locally, not a published default. For development, use `npm run dev` with the preserved `.env.local` API URL.

## Scripts

- `npm run dev`
- `npm run build`
- `npm run lint`
- `npm run typecheck`
- `npm run test`
- `npm run test:e2e`

## Security and limitations

- Server-side upload checks accept only JPEG and PNG signatures and reject request bodies over 10 MB.
- Uploads, results, exports, readiness and saved images require valid server-side sessions and account ownership. History is transactional SQLite storage.
- CORS is restricted to configured localhost development ports.
- Client-side file validation is UX only; server-side validation remains mandatory.
- DICOM support is not included; current uploads assume JPG/PNG.
- Local accounts use salted PBKDF2 hashes; sessions are revocable HttpOnly/SameSite cookies. Jobs, storage and request bodies are bounded. This loopback HTTP demo is not a remote deployment.

## AI assistance

Parts of this project were generated or revised with AI-assisted programming tools. A human must review the implementation, dependencies, dataset permissions, security controls, and model behavior before reuse or distribution.

## Not yet implemented

- Remote deployment with TLS, Secure cookies, operational monitoring, managed account provisioning/recovery and audit persistence.
- Clinical validation, regulatory review, and DICOM support.
- An approved model distribution location and verified historical checkpoint permissions.
