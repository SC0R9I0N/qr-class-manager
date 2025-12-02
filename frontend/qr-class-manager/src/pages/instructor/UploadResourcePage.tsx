import React, { useState } from "react";
import { uploadMaterialsZip } from "../../api/materials";
import "./UploadResourcePage.css"

const UploadResourcePage: React.FC = () => {
    const [file, setFile] = useState<File | null>(null);
    const [status, setStatus] = useState<string | null>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selected = e.target.files?.[0] || null;
        setFile(selected);
    };

    const handleUpload = async () => {
        if (!file) {
            setStatus("Please select a .zip file first.");
            return;
        }

        if (!file.name.endsWith(".zip")) {
            setStatus("File must be a .zip.");
            return;
        }

        try {
            setStatus("Uploading...");
            await uploadMaterialsZip(file);
            setStatus("Upload successful!");
        } catch (e) {
            setStatus(`Upload failed: ${(e as Error).message}`);
        }
    };

    return (
        <div className="upload-container">
            <div className="upload-card">
                <h1>Upload Course Materials</h1>

                <input className="file-input"type="file" accept=".zip" onChange={handleFileChange}/>

                <button 
                    className="upload-class-btn"
                    onClick={handleUpload}>
                    Upload
                </button>
                {status}
            </div>
        </div>
    );
};

export default UploadResourcePage;