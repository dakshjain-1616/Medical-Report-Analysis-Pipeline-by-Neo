# medical report analysis pipeline - by Neo

## Single-Command Execution
To run the entire diagnostic pipeline, including starting the secure API server, processing pending medical studies, and performing a final system validation, execute:

```bash
./run_pipeline.sh
```

The script handles virtual environment activation, background server management, and automated cleanup. Logs are stored in the `./logs` directory.

## Overview
This project implements a HIPAA-compliant medical imaging and diagnostic assistance system. It leverages state-of-the-art vision models and secure infrastructure to process X-rays and CT scans, providing automated segmentation and clinical report generation while ensuring the highest standards of data privacy.

## Core Features
- **HIPAA-Compliant Infrastructure**: Secure handling of Protected Health Information (PHI) through end-to-end encryption and strict de-identification protocols.
- **MedSAM Integration**: Integration of the Medical Segmentation Anything Model for high-accuracy anatomical structure segmentation.
- **RadBERT Integration**: Use of RadBERT for generating structured, clinically relevant radiology reports.
- **Multimodal Fusion**: A pipeline that combines image features with patient history and demographics for comprehensive risk assessment.

## Security Architecture
The system utilizes advanced security measures implemented in `utils/security.py`:
- **Fernet Encryption**: AES-128 encryption in CBC mode with HMAC for data at rest. All sensitive files in `secure_storage/` are encrypted.
- **Role-Based Access Control (RBAC)**: Fine-grained access management ensuring only authorized personnel can trigger diagnostic pipelines or view results.
- **Audit Logging**: Comprehensive logging to `logs/audit.log` that tracks all access and processing events without leaking PHI.
- **TLS/SSL Encryption**: Secure data in transit using the provided `cert.pem` and `key.pem` certificates.

## Environment Setup
The system is optimized for a **Tesla V100 GPU** environment (16GB VRAM) to handle heavy model inference and DICOM processing.
- **GPU Acceleration**: CUDA 11.0+ support for MedSAM and RadBERT.
- **Memory Management**: Configured to handle large medical studies (up to 512MB) within 16-32GB RAM constraints.

## Execution Guide

### 1. Activate Virtual Environment
Ensure you are in the project root and activate the pre-configured environment:
```bash
source venv/bin/activate
```

### 2. Security Infrastructure Setup
Generate or verify the presence of SSL certificates for the secure API:
- `cert.pem`: SSL Certificate
- `key.pem`: Private Key

If they are missing, the system expects them for the `FastAPI` HTTPS server to start.

### 3. Running the Diagnostic API
Start the secure backend server:
```bash
python api.py
```
The API handles study submission, encryption, and secure metadata storage in `metadata.db`.

### 4. Processing Studies with Solver
To trigger the diagnostic pipeline (Segmentation + Report Generation + Fusion):
```bash
python solver.py
```
The `solver.py` script picks up pending studies, decrypts data into memory for processing, runs the MedSAM/RadBERT models, and saves the encrypted results.

### 5. Verification
Run the verification suite to ensure pipeline integrity and compliance:
```bash
python final_verify.py
```

## Directory Structure
- `api.py`: Secure interface for study ingestion.
- `solver.py`: Core processing engine for model inference.
- `utils/security.py`: Fernet encryption and RBAC logic.
- `data/`: Raw and processed medical datasets.
- `secure_storage/`: Encrypted patient data.
- `logs/audit.log`: HIPAA-compliant audit trails.