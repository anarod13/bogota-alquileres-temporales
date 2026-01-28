#!/usr/bin/env dotnet-script
using System;
using System.IO;
using System.Linq;
using System.Text.Json;

public class Program
{
    public static void Main(string[] args)
    {
        // Get script directory - use current working directory
        // When run from bash, this will be the directory where the script is executed from
        string scriptDir = Directory.GetCurrentDirectory();

        // Get input file or use default
        string harFile = Path.Combine(scriptDir, "../sources/har/141883_all_items_a.har");
        string outputFolder = Path.Combine(scriptDir, "har_results");

        if (args.Length > 0 && !string.IsNullOrEmpty(args[0]))
        {
            harFile = Path.IsPathRooted(args[0]) ? args[0] : Path.Combine(Directory.GetCurrentDirectory(), args[0]);
        }

        // Resolve relative paths
        harFile = Path.GetFullPath(harFile);
        outputFolder = Path.GetFullPath(outputFolder);

        Console.WriteLine($"Processing HAR file: {harFile}");
        Console.WriteLine($"Output folder: {outputFolder}");

        if (!File.Exists(harFile))
        {
            Console.WriteLine($"Error: File '{harFile}' not found.");
            Console.WriteLine($"Current directory: {Directory.GetCurrentDirectory()}");
            Console.WriteLine("Usage: dotnet-script parse-har.csx [filename.har]");
            Environment.Exit(1);
            return;
        }

        // Create output directory
        try
        {
            Directory.CreateDirectory(outputFolder);
            Console.WriteLine($"Created output directory: {outputFolder}\n");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Warning: Could not create output directory: {ex.Message}");
        }

        try
        {
            // Read and parse HAR file
            Console.WriteLine("Reading HAR file...");
            string harContent = File.ReadAllText(harFile);
            Console.WriteLine($"HAR file size: {harContent.Length} characters");

            using JsonDocument harDoc = JsonDocument.Parse(harContent);

            // Get entries with error handling
            if (!harDoc.RootElement.TryGetProperty("log", out var logElement))
            {
                Console.WriteLine("Error: HAR file does not contain 'log' property");
                Environment.Exit(1);
                return;
            }

            if (!logElement.TryGetProperty("entries", out var entries))
            {
                Console.WriteLine("Error: HAR file does not contain 'entries' property");
                Environment.Exit(1);
                return;
            }

            Console.WriteLine($"Found {entries.GetArrayLength()} total entries\n");

            // Find JSON responses
            int jsonCount = 0;
            int skippedCount = 0;
            int errorCount = 0;

            foreach (var entry in entries.EnumerateArray())
            {
                try
                {
                    if (!entry.TryGetProperty("response", out var response))
                    {
                        skippedCount++;
                        continue;
                    }

                    if (!response.TryGetProperty("content", out var content))
                    {
                        skippedCount++;
                        continue;
                    }

                    if (!content.TryGetProperty("mimeType", out var mimeTypeElement))
                    {
                        skippedCount++;
                        continue;
                    }

                    string mimeType = mimeTypeElement.GetString() ?? "";
                    string url = "";

                    if (entry.TryGetProperty("request", out var request) &&
                        request.TryGetProperty("url", out var urlElement))
                    {
                        url = urlElement.GetString() ?? "";
                    }

                    if (mimeType.Contains("json", StringComparison.OrdinalIgnoreCase) &&
                        content.TryGetProperty("text", out var textElement))
                    {
                        jsonCount++;
                        string jsonText = textElement.GetString() ?? "";

                        if (string.IsNullOrEmpty(jsonText))
                        {
                            Console.WriteLine($"  [{jsonCount}] ⚠ Skipped (empty response): {url}");
                            skippedCount++;
                            continue;
                        }

                        Console.WriteLine($"=== JSON Response #{jsonCount} ===");
                        Console.WriteLine($"URL: {url}");
                        Console.WriteLine($"Size: {jsonText.Length:N0} characters ({jsonText.Length / 1024.0 / 1024.0:F2} MB)");

                        try
                        {
                            // Parse the inner JSON
                            using JsonDocument jsonDoc = JsonDocument.Parse(jsonText);
                            var options = new JsonSerializerOptions { WriteIndented = true };
                            string prettyJson = JsonSerializer.Serialize(jsonDoc.RootElement, options);

                            // Generate filename from URL or use index
                            string outputFile = GenerateFilename(url, jsonCount);
                            string outputPath = Path.Combine(outputFolder, outputFile);

                            File.WriteAllText(outputPath, prettyJson);
                            Console.WriteLine($"✓ Saved to: {outputPath}\n");
                        }
                        catch (JsonException jsonEx)
                        {
                            errorCount++;
                            Console.WriteLine($"✗ Could not parse JSON: {jsonEx.Message}");

                            // Save malformed JSON as text file
                            string txtFile = Path.Combine(outputFolder, $"response_{jsonCount}_malformed.txt");
                            File.WriteAllText(txtFile, $"URL: {url}\nError: {jsonEx.Message}\n\n{jsonText}");
                            Console.WriteLine($"  Saved malformed JSON as: {txtFile}\n");
                        }
                    }
                    else
                    {
                        skippedCount++;
                    }
                }
                catch (Exception ex)
                {
                    errorCount++;
                    Console.WriteLine($"✗ Error processing entry: {ex.Message}");
                }
            }

            Console.WriteLine($"\n{new string('=', 60)}");
            Console.WriteLine("SUMMARY");
            Console.WriteLine($"{new string('=', 60)}");
            Console.WriteLine($"Total entries processed: {entries.GetArrayLength()}");
            Console.WriteLine($"JSON responses extracted: {jsonCount}");
            Console.WriteLine($"Skipped entries: {skippedCount}");
            Console.WriteLine($"Errors: {errorCount}");
            Console.WriteLine($"Output directory: {outputFolder}");
        }
        catch (JsonException ex)
        {
            Console.WriteLine($"JSON Error: {ex.Message}");
            Console.WriteLine($"Position: {ex.BytePositionInLine}");
            Environment.Exit(1);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error: {ex.Message}");
            Console.WriteLine($"Stack trace: {ex.StackTrace}");
            Environment.Exit(1);
        }
    }

    static string GenerateFilename(string url, int index)
    {
        if (string.IsNullOrEmpty(url))
        {
            return $"response_{index}.json";
        }

        try
        {
            var uri = new Uri(url);
            var segments = uri.Segments.Where(s => !string.IsNullOrWhiteSpace(s)).ToList();

            if (segments.Count > 0)
            {
                string lastSegment = segments.Last().TrimEnd('/');
                if (!string.IsNullOrEmpty(lastSegment) && lastSegment.Length < 100)
                {
                    // Sanitize filename
                    string sanitized = string.Join("_", lastSegment.Split(Path.GetInvalidFileNameChars()));
                    return $"{sanitized}_{index}.json";
                }
            }
        }
        catch
        {
            // Fall through to default
        }

        return $"response_{index}.json";
    }
}