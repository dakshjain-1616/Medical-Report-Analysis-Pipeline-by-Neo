import SimpleITK as sitk
import numpy as np
import os
import json
import uuid
from utils.security import EncryptionHandler
import logging

logger = logging.getLogger("data_pipeline")

class MedicalDataProcessor:
    def __init__(self, secure_storage_path="/root/MedicalReportAnalysis/secure_storage"):
        self.storage_path = secure_storage_path
        self.encryption = EncryptionHandler()
        os.makedirs(self.storage_path, exist_ok=True)

    def parse_dicom_or_nifti(self, file_path):
        """Load medical image using SimpleITK."""
        try:
            image = sitk.ReadImage(file_path)
            image_array = sitk.GetArrayFromImage(image)
            return image, image_array
        except Exception as e:
            logger.error(f"Error parsing image {file_path}: {str(e)}")
            return None, None

    def normalize_image(self, image_array):
        """Standardize image intensity values."""
        img_min = np.min(image_array)
        img_max = np.max(image_array)
        if img_max - img_min == 0:
            return image_array
        normalized = (image_array - img_min) / (img_max - img_min)
        return normalized.astype(np.float32)

    def deidentify_dicom(self, image):
        """Strip PHI from DICOM metadata for research."""
        # SimpleITK image metadata handling
        keys = image.GetMetaDataKeys()
        # In a real scenario, we'd whitelist keys instead of just stripping all
        # For simplicity, we create a new image without sensitive metadata
        new_image = sitk.GetImageFromArray(sitk.GetArrayFromImage(image))
        new_image.SetSpacing(image.GetSpacing())
        new_image.SetOrigin(image.GetOrigin())
        new_image.SetDirection(image.GetDirection())
        return new_image

    def secure_save_study(self, image_array, patient_metadata, study_id=None):
        """Encrypt and save medical volume and metadata."""
        if not study_id:
            study_id = str(uuid.uuid4())
        
        # Save image as numpy encrypted
        img_bytes = image_array.tobytes()
        encrypted_img = self.encryption.encrypt_data(img_bytes)
        
        study_dir = os.path.join(self.storage_path, study_id)
        os.makedirs(study_dir, exist_ok=True)
        
        with open(os.path.join(study_dir, "image.enc"), "wb") as f:
            f.write(encrypted_img)
            
        # Save metadata encrypted
        meta_bytes = json.dumps(patient_metadata).encode()
        encrypted_meta = self.encryption.encrypt_data(meta_bytes)
        
        with open(os.path.join(study_dir, "metadata.enc"), "wb") as f:
            f.write(encrypted_meta)
            
        return study_id

    def ingest_demographics(self, json_data):
        """Process clinical history and demographics."""
        # Validates and maps structure
        return {
            "age": json_data.get("age"),
            "gender": json_data.get("gender"),
            "history": json_data.get("clinical_history", ""),
            "anonymized_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, str(json_data.get("patient_id"))))
        }

if __name__ == "__main__":
    # Smoke test
    processor = MedicalDataProcessor()
    dummy_img = np.random.rand(10, 512, 512).astype(np.float32)
    meta = {"patient_id": "12345", "age": 45, "gender": "M"}
    sid = processor.secure_save_study(dummy_img, meta)
    print(f"Securely saved study: {sid}")