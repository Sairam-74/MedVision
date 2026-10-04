# MedVision AI

MedVision AI is a student research prototype for bone-fracture segmentation and severity heuristics from JPG/PNG X-ray images. It includes a PyTorch backend and a React/Vite frontend for local demonstrations.

## Important Safety Notice

**This project is not for clinical use.** It has not been clinically validated, approved by a medical regulator, or tested for use in diagnosis or treatment. Results are experimental and require qualified human review. Do not upload identifiable patient data.

## Dataset

The training and demonstration pipeline can use **FracAtlas**, a dataset for fracture classification, localization, and segmentation of musculoskeletal radiographs.

- Project link: <https://github.com/ibrahimhamamci/FracAtlas> **TO VERIFY before redistribution**
- Citation: Hamamci et al., *FracAtlas: A Dataset for Fracture Classification, Localization and Segmentation of Musculoskeletal Radiographs.* **TO VERIFY against the dataset's official citation.**
- **License and redistribution terms: TO VERIFY with the dataset provider before sharing the archive or derived images.**

The `FracAtlas.zip` archive is intentionally excluded from version control. Obtain it only from an authorized source, confirm its terms, and place it at the project root if local training or dataset diagnostics are required.

## Model

The trained checkpoint `best_model.pt` is intentionally excluded from version control because it is a large binary artifact. Obtain the checkpoint from the project owner or an approved model-storage location, verify its provenance, and place it at the project root. Do not redistribute it until its training-data and model-license permissions are confirmed.

## Setup

1. Install the Python dependencies from `requirements.txt` in the project's virtual environment.
2. Install the frontend dependencies with `npm ci`.
3. Copy `.env.example` to `.env` for frontend settings. Set backend environment variables `MEDVISION_DEMO_PASSWORD` and `MEDVISION_LOCAL_ACCESS_TOKEN` in the local shell when using the demo login. Never commit `.env` or `.env.local`.
4. Start the backend with `uvicorn backend_service:app --reload --port 8000`.
5. Start the frontend with `npm run dev`.

## Scripts

- `npm run dev`
- `npm run build`
- `npm run lint`
- `npm run typecheck`
- `npm run test`
- `npm run test:e2e`

## Security and limitations

- Server-side upload checks accept only JPEG and PNG signatures and reject request bodies over 10 MB.
- Upload endpoints currently do not require authentication. This is a known local-demo limitation and must be fixed before deployment.
- CORS is restricted to configured localhost development ports.
- Client-side file validation is UX only; server-side validation remains mandatory.
- DICOM support is not included; current uploads assume JPG/PNG.
- The backend uses in-memory demo users and is not a production authentication system.

## AI assistance

Parts of this project were generated or revised with AI-assisted programming tools. A human must review the implementation, dependencies, dataset permissions, security controls, and model behavior before reuse or distribution.

## Not yet implemented

- Production authentication, authorization, audit persistence, and secure session handling.
- Clinical validation, regulatory review, and DICOM support.
- Confirmed dataset licensing and an approved model distribution location.
