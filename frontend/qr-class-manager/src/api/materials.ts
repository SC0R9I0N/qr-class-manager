import { apiGet, apiPost } from "./api";

export interface Material {
    id: string;
    class_id?: string;
    url: string;
    uploaded_at: string;
}

export function fetchMaterials(): Promise<Material[]> {
    return apiGet<Material[]>("/materials");
}

// In api/materials.ts

// Helper to convert File to Base64
const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => {
            // Remove the data:application/zip;base64, prefix
            const base64String = (reader.result as string).split(',')[1];
            resolve(base64String);
        };
        reader.onerror = error => reject(error);
    });
};

export async function uploadMaterialsZip(file: File, sessionId: string): Promise<Material> {
    const base64File = await fileToBase64(file);

    // We send a standard JSON body that matches your current Lambda logic
    const body = {
        session_id: sessionId,
        filename: file.name,
        file_content: base64File // Matches backend: body.get('file_content')
    };

    // Use apiPost instead of apiUpload to send JSON
    return apiPost<Material>("/materials", body);
}