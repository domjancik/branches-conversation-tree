export class ApiService {
  async loadConfig(){
    const res = await fetch('/api/config');
    if(!res.ok) throw new Error('Failed to load config');
    return res.json();
  }
  async loadTreeData(){
    const res = await fetch('/api/tree-data');
    if(!res.ok) throw new Error('Failed to load tree data');
    return res.json();
  }
  async loadImages(recordingId){
    const res = await fetch(`/api/recordings/${recordingId}/images`);
    if(!res.ok) return [];
    return res.json();
  }
}
