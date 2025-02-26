import whisper
import ollama
import requests
import json
import sys
import os
import time
from datetime import datetime
host = "http://127.0.0.1:8888"

# STYLE_POOL = [
# #   "Misc Dreamscape",
# #   "MRE Dark Dream",
# #   "MRE Bad Dream",
#   "MRE Surreal Painting",
#   "Artstyle Surrealist",
# #   "Artstyle Psychedelic",
# #   "Photo Long Exposure",
# #   "Mk Suminagashi",
#   "Mk Ukiyo E",
#   "MRE Lyrical Geometry",
#   "Dmt Art Style",
# #   "Futuristic Vaporwave",
# #   "Abstract Expressionism"
# ]

STYLE_POOL = ["Fooocus V2","Random Style","Fooocus Enhance","Fooocus Semi Realistic","Fooocus Sharp","Fooocus Masterpiece","Fooocus Photograph","Fooocus Negative","Fooocus Cinematic","Fooocus Pony","SAI 3D Model","SAI Analog Film","SAI Anime","SAI Cinematic","SAI Comic Book","SAI Craft Clay","SAI Digital Art","SAI Enhance","SAI Fantasy Art","SAI Isometric","SAI Line Art","SAI Lowpoly","SAI Neonpunk","SAI Origami","SAI Photographic","SAI Pixel Art","SAI Texture","MRE Cinematic Dynamic","MRE Spontaneous Picture","MRE Artistic Vision","MRE Dark Dream","MRE Gloomy Art","MRE Bad Dream","MRE Underground","MRE Surreal Painting","MRE Dynamic Illustration","MRE Undead Art","MRE Elemental Art","MRE Space Art","MRE Ancient Illustration","MRE Brave Art","MRE Heroic Fantasy","MRE Dark Cyberpunk","MRE Lyrical Geometry","MRE Sumi E Symbolic","MRE Sumi E Detailed","MRE Manga","MRE Anime","MRE Comic","Ads Advertising","Ads Automotive","Ads Corporate","Ads Fashion Editorial","Ads Food Photography","Ads Gourmet Food Photography","Ads Luxury","Ads Real Estate","Ads Retail","Artstyle Abstract","Artstyle Abstract Expressionism","Artstyle Art Deco","Artstyle Art Nouveau","Artstyle Constructivist","Artstyle Cubist","Artstyle Expressionist","Artstyle Graffiti","Artstyle Hyperrealism","Artstyle Impressionist","Artstyle Pointillism","Artstyle Pop Art","Artstyle Psychedelic","Artstyle Renaissance","Artstyle Steampunk","Artstyle Surrealist","Artstyle Typography","Artstyle Watercolor","Futuristic Biomechanical","Futuristic Biomechanical Cyberpunk","Futuristic Cybernetic","Futuristic Cybernetic Robot","Futuristic Cyberpunk Cityscape","Futuristic Futuristic","Futuristic Retro Cyberpunk","Futuristic Retro Futurism","Futuristic Sci Fi","Futuristic Vaporwave","Game Bubble Bobble","Game Cyberpunk Game","Game Fighting Game","Game Gta","Game Mario","Game Minecraft","Game Pokemon","Game Retro Arcade","Game Retro Game","Game Rpg Fantasy Game","Game Strategy Game","Game Streetfighter","Game Zelda","Misc Architectural","Misc Disco","Misc Dreamscape","Misc Dystopian","Misc Fairy Tale","Misc Gothic","Misc Grunge","Misc Horror","Misc Kawaii","Misc Lovecraftian","Misc Macabre","Misc Manga","Misc Metropolis","Misc Minimalist","Misc Monochrome","Misc Nautical","Misc Space","Misc Stained Glass","Misc Techwear Fashion","Misc Tribal","Misc Zentangle","Papercraft Collage","Papercraft Flat Papercut","Papercraft Kirigami","Papercraft Paper Mache","Papercraft Paper Quilling","Papercraft Papercut Collage","Papercraft Papercut Shadow Box","Papercraft Stacked Papercut","Papercraft Thick Layered Papercut","Photo Alien","Photo Film Noir","Photo Glamour","Photo Hdr","Photo Iphone Photographic","Photo Long Exposure","Photo Neon Noir","Photo Silhouette","Photo Tilt Shift","Cinematic Diva","Abstract Expressionism","Academia","Action Figure","Adorable 3D Character","Adorable Kawaii","Art Deco","Art Nouveau","Astral Aura","Avant Garde","Baroque","Bauhaus Style Poster","Blueprint Schematic Drawing","Caricature","Cel Shaded Art","Character Design Sheet","Classicism Art","Color Field Painting","Colored Pencil Art","Conceptual Art","Constructivism","Cubism","Dadaism","Dark Fantasy","Dark Moody Atmosphere","Dmt Art Style","Doodle Art","Double Exposure","Dripping Paint Splatter Art","Expressionism","Faded Polaroid Photo","Fauvism","Flat 2d Art","Fortnite Art Style","Futurism","Glitchcore","Glo Fi","Googie Art Style","Graffiti Art","Harlem Renaissance Art","High Fashion","Idyllic","Impressionism","Infographic Drawing","Ink Dripping Drawing","Japanese Ink Drawing","Knolling Photography","Light Cheery Atmosphere","Logo Design","Luxurious Elegance","Macro Photography","Mandola Art","Marker Drawing","Medievalism","Minimalism","Neo Baroque","Neo Byzantine","Neo Futurism","Neo Impressionism","Neo Rococo","Neoclassicism","Op Art","Ornate And Intricate","Pencil Sketch Drawing","Pop Art 2","Rococo","Silhouette Art","Simple Vector Art","Sketchup","Steampunk 2","Surrealism","Suprematism","Terragen","Tranquil Relaxing Atmosphere","Sticker Designs","Vibrant Rim Light","Volumetric Lighting","Watercolor 2","Whimsical And Playful","Mk Chromolithography","Mk Cross Processing Print","Mk Dufaycolor Photograph","Mk Herbarium","Mk Punk Collage","Mk Mosaic","Mk Van Gogh","Mk Coloring Book","Mk Singer Sargent","Mk Pollock","Mk Basquiat","Mk Andy Warhol","Mk Halftone Print","Mk Gond Painting","Mk Albumen Print","Mk Aquatint Print","Mk Anthotype Print","Mk Inuit Carving","Mk Bromoil Print","Mk Calotype Print","Mk Color Sketchnote","Mk Cibulak Porcelain","Mk Alcohol Ink Art","Mk One Line Art","Mk Blacklight Paint","Mk Carnival Glass","Mk Cyanotype Print","Mk Cross Stitching","Mk Encaustic Paint","Mk Embroidery","Mk Gyotaku","Mk Luminogram","Mk Lite Brite Art","Mk Mokume Gane","Pebble Art","Mk Palekh","Mk Suminagashi","Mk Scrimshaw","Mk Shibori","Mk Vitreous Enamel","Mk Ukiyo E","Mk Vintage Airline Poster","Mk Vintage Travel Poster","Mk Bauhaus Style","Mk Afrofuturism","Mk Atompunk","Mk Constructivism","Mk Chicano Art","Mk De Stijl","Mk Dayak Art","Mk Fayum Portrait","Mk Illuminated Manuscript","Mk Kalighat Painting","Mk Madhubani Painting","Mk Pictorialism","Mk Pichwai Painting","Mk Patachitra Painting","Mk Samoan Art Inspired","Mk Tlingit Art","Mk Adnate Style","Mk Ron English Style","Mk Shepard Fairey Style"]
# STYLE_POOL = ["Mk Lite Brite Art", "Mk Gyotaku", "Mk Luminogram"]
# STYLE_POOL = ["Mk Shepard Fairey Style", "Faded Polaroid Photo", "SAI Analog Film"]

# PROMPT_SUFFIX = " Colorful. Black background. Black borders. No text. Detailed view."
PROMPT_SUFFIX = ""

def get_image_prompts(text: str, ollama_model: str = "llama3.1:8b"):
    model = ollama.generate(
        model=ollama_model,
        prompt=f"Generate 10 image prompts for the following text: {text}. Respond in a JSON array format only, no other text.",
        stream=False
    )
    print(model.response)
    parsed_response = json.loads(model.response)
    return parsed_response

def text2img(params: dict) -> dict:
    """
    text to image
    """
    result = requests.post(url=f"{host}/v1/generation/text-to-image",
                           data=json.dumps(params),
                           headers={"Content-Type": "application/json"})
    return result.json()

def inpaint_image(params: dict) -> dict:
    result = requests.post(url=f"{host}/v1/generation/inpainting",
                           data=json.dumps(params),
                           headers={"Content-Type": "application/json"})
    return result.json()

def get_image_file_name(file_base_name: str, index: int, style: str):
    iso_date = datetime.now().isoformat()
    file_name = f"{file_base_name}_{index}_{style}_{iso_date}.png"
    file_name = file_name.replace(":", "-").replace(" ", "-")
    return file_name

def inpaint_and_store_image(params: dict, index: int, file_base_name: str, style: str):
    time_start = time.time()
    result = inpaint_image(params)
    print(json.dumps(result, indent=4))
    image_url = result[0]["url"]
    image_data = requests.get(image_url).content
    file_name = get_image_file_name(file_base_name, index, style)
    with open(file_name, "wb") as f:
        f.write(image_data)
    print(f"Wrote image to {file_name}")
    print(f"Time taken: {time.time() - time_start} seconds")

def generate_and_store_image(prompt: str, index: int, file_base_name: str, style: str):
    print(f"Generating image for prompt: {prompt}")
    time_start = time.time()
    params = {
        "prompt": prompt,
        "aspect_ratios_selection": "1024*1024",
        # "aspect_ratios_selection": "256*256",
        # "performance_selection": "Extreme Speed",
        "performance_selection": "Speed",
        # "style_selection": random.choice(STYLE_POOL),
        "style_selections": [style],
    }
    result = text2img(params)
    print(json.dumps(result, indent=4))
    image_url = result[0]["url"]
    image_data = requests.get(image_url).content
    iso_date = datetime.now().isoformat()
    file_name = f"{file_base_name}_{index}_{style}_{iso_date}.png"
    file_name = file_name.replace(":", "-").replace(" ", "-")

    with open(file_name, "wb") as f:
        f.write(image_data)

    print(f"Wrote image to {file_name}")
    print(f"Time taken: {time.time() - time_start} seconds")


def generate_images(prompts: list[str], file_base_name: str):
    for index, prompt in enumerate(prompts):
        for style in STYLE_POOL:
            generate_and_store_image(prompt + PROMPT_SUFFIX, index, file_base_name, style)

def transcribe_audio(source_file: str) -> str:
    model = whisper.load_model("medium")  # Can use "tiny", "small", "medium", or "large"
    result = model.transcribe(source_file, language="en", task="translate")  # Auto-detects Hebrew & English
    print(json.dumps(result, indent=4))
    return result["text"]

def main(source_file: str, target_file_base_name: str, ollama_model: str = "llama3.1:8b"):
    # file_exists = os.path.exists(source_file)
    # if not file_exists:
    #     print(f"file {source_file} does not exist")
    #     return

    # print(f"transcribing audio from {source_file}...")
    # text = transcribe_audio(source_file)
    # print(text)
    # open(f"{target_file_base_name}.txt", "w").write(text)

    # prompts = get_image_prompts(text, ollama_model)
    # print(prompts)
    # open(f"{target_file_base_name}_prompts.json", "w").write(json.dumps(prompts, indent=4))

    # prompts = ["A school of colorful fish swimming in an underwater coral reef.", "Close-up photo of a fish's book with strange writing on its pages.", "An old, wise-looking fish with glasses reading a book written in ancient symbols.", "Fish holding up their hands as if they were signing and making a unique hand gesture to show the meaning of a word on a book.", "A group of diverse fish staring at each other curiously while one of them has an open book in front of their face, showing unusual writing", "An underwater scene with bubbles and bioluminescence illuminating strange language written in a fish's book.", "A single fish with large eyes and a thoughtful expression, holding up a book covered in unknown symbols to the camera.", "Different kinds of fish talking in groups, with some reading books filled with elaborate scripts on their fins", "Fish swimming in a school formation, each one has a different color and shape, and they all have books in their hands.  They are creating a strange, but beautiful code of communication.", "A group of diverse fish looking at the camera, as though they're speaking directly to the viewer about their language."]
    # prompts = prompts[0:3]
    prompts = ["Snake with a meditating skeleton", "Meditating skeleton with a snake"]

    generate_images(prompts, target_file_base_name)

if __name__ == "__main__":
    source_file = sys.argv[1]
    target_file_base_name = sys.argv[2]
    ollama_model = sys.argv[3]
    
    main(source_file, target_file_base_name, ollama_model)

