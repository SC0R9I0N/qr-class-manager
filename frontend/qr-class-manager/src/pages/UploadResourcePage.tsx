import React from "react";

const UploadResourcePage: React.FC = () => {
    const handleUploadClick = () => {
        alert("Upload flow will go here!");
    };

    return (
        <div style={{ padding: 20 }}>
            <h1>Upload Resource</h1>

            <button
                onClick={handleUploadClick}
                style={{
                    padding: "10px 20px",
                    cursor: "pointer",
                }}
            >
                Select File to Upload
            </button>
        </div>
    );
};

export default UploadResourcePage;