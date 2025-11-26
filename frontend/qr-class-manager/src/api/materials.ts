import { apiGet, apiUpload } from "./api";

export interface Material {
    id: string;
    class_id?: string;
    url: string;
    uploaded_at: string;
}

export function fetchMaterials(): Promise<Material[]> {
    return apiGet<Material[]>("/materials");
}

export function uploadMaterialsZip(file: File): Promise<Material> {
    const formData = new FormData();
    formData.append("file", file); // backend should look for "file"
    return apiUpload<Material>("/materials", formData);
}