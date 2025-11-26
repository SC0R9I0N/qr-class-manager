import React, { useState } from "react";
import { uploadMaterialsZip } from "../api/materials";

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
        <div style={{ padding: 20 }}>
            <h1>Upload Course Materials</h1>

            <input type="file" accept=".zip" onChange={handleFileChange} />
            <br /><br />

            <button onClick={handleUpload} style={{ padding: "8px 16px" }}>
                Upload
            </button>

            {status && <p style={{ marginTop: 10 }}>{status}</p>}
        </div>
    );
};

export default UploadResourcePage;