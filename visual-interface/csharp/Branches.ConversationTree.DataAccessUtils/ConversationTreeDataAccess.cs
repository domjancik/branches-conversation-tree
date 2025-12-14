// For examples, see:
// https://thegraybook.vvvv.org/reference/extending/writing-nodes.html#examples

namespace Branches.ConversationTree;
using System.Text.Json;
using System.Text.Json.Serialization;

public class AudioRecordingCreateRequest
{
    [JsonPropertyName("audio_file_path")]
    public string AudioFilePath { get; set; }
    
    [JsonPropertyName("parent_audio_recording_id")]
    public int? ParentAudioRecordingId { get; set; }
    
    [JsonPropertyName("parent_time")]
    public float? ParentTime { get; set; }
}

public class AudioRecordingResponse
{
    [JsonPropertyName("id")]
    public int Id { get; set; }
    
    [JsonPropertyName("audio_file_path")]
    public string AudioFilePath { get; set; }
    
    [JsonPropertyName("created_date")]
    public string CreatedDate { get; set; }
    
    [JsonPropertyName("updated_date")]
    public string UpdatedDate { get; set; }
    
    [JsonPropertyName("parent_audio_recording")]
    public int? ParentAudioRecording { get; set; }
    
    [JsonPropertyName("parent_time")]
    public float? ParentTime { get; set; }
}

public class TranscriptionStatus
{
    [JsonPropertyName("status")]
    public string Status { get; set; }
    
    [JsonPropertyName("text")]
    public string Text { get; set; }
    
    [JsonPropertyName("updated_date")]
    public string UpdatedDate { get; set; }
}

public class ImageGenerationItem
{
    [JsonPropertyName("id")]
    public int Id { get; set; }
    
    [JsonPropertyName("prompt")]
    public string Prompt { get; set; }
    
    [JsonPropertyName("status")]
    public string Status { get; set; }
    
    [JsonPropertyName("progress")]
    public float? Progress { get; set; }
    
    [JsonPropertyName("image_file_path")]
    public string ImageFilePath { get; set; }
    
    [JsonPropertyName("duration")]
    public float? Duration { get; set; }
    
    [JsonPropertyName("seed")]
    public int? Seed { get; set; }
    
    [JsonPropertyName("created_date")]
    public string CreatedDate { get; set; }
    
    [JsonPropertyName("updated_date")]
    public string UpdatedDate { get; set; }
}

public class ImageGenerationStatus
{
    [JsonPropertyName("total")]
    public int Total { get; set; }
    
    [JsonPropertyName("pending")]
    public int Pending { get; set; }
    
    [JsonPropertyName("generating")]
    public int Generating { get; set; }
    
    [JsonPropertyName("completed")]
    public int Completed { get; set; }
    
    [JsonPropertyName("failed")]
    public int Failed { get; set; }
    
    [JsonPropertyName("progress")]
    public float Progress { get; set; }
    
    [JsonPropertyName("generations")]
    public List<ImageGenerationItem> Generations { get; set; }
}

public class ProcessingStatusResponse
{
    [JsonPropertyName("recording_id")]
    public int RecordingId { get; set; }
    
    [JsonPropertyName("transcription")]
    public TranscriptionStatus Transcription { get; set; }
    
    [JsonPropertyName("image_generation")]
    public ImageGenerationStatus ImageGeneration { get; set; }
    
    [JsonPropertyName("overall_status")]
    public string OverallStatus { get; set; }
    
    [JsonPropertyName("created_date")]
    public string CreatedDate { get; set; }
    
    [JsonPropertyName("updated_date")]
    public string UpdatedDate { get; set; }
}

public static class ConversationTreeDataAccess
{
    private static readonly HttpClient httpClient = new HttpClient() { BaseAddress = new Uri("http://localhost:8000") };

    public static async Task<AudioRecordingResponse> CreateNewRecording(string audioFilePath, int? parentRecordingId = null, float? parentTime = null)
    {
        var request = new AudioRecordingCreateRequest
        {
            AudioFilePath = audioFilePath,
            ParentAudioRecordingId = parentRecordingId,
            ParentTime = parentTime
        };

        var json = JsonSerializer.Serialize(request);
        var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json");

        var response = await httpClient.PostAsync("/recordings/", content);
        response.EnsureSuccessStatusCode();

        var responseJson = await response.Content.ReadAsStringAsync();
        return JsonSerializer.Deserialize<AudioRecordingResponse>(responseJson);
    }

    public static async Task<List<AudioRecordingResponse>> GetRecordingTree(int recordingId)
    {
        var response = await httpClient.GetAsync($"/recordings/{recordingId}/tree");
        response.EnsureSuccessStatusCode();

        var responseJson = await response.Content.ReadAsStringAsync();
        return JsonSerializer.Deserialize<List<AudioRecordingResponse>>(responseJson);
    }

    public static async Task<ProcessingStatusResponse> GetProcessingStatus(int recordingId)
    {
        var response = await httpClient.GetAsync($"/recordings/{recordingId}/processing-status");
        response.EnsureSuccessStatusCode();

        var responseJson = await response.Content.ReadAsStringAsync();
        return JsonSerializer.Deserialize<ProcessingStatusResponse>(responseJson);
    }
}