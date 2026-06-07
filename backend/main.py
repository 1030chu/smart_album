import os
import shutil
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")

if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

device = "cuda" if torch.cuda.is_available() else "cpu"
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

CATEGORY_MAP = {

    "반려동물": ["a close-up of a cute dog or cat", "my pet animal", "pet sitting on the floor", "dog", "cat", "pet"],
    "야생동물": ["wild animal in nature", "birds in the sky", "forest wildlife", "wildlife", "animal"],
    "수중생물": ["fish swimming in an aquarium", "sea creatures", "underwater photography", "fish", "aquarium"],
    "식물과 꽃": ["beautiful flowers in a garden", "houseplants in pots", "blooming flowers", "flower", "plant"],
    "산과 풍경": ["mountain peaks and ranges", "breathtaking landscape view", "nature scenery", "mountain", "landscape"],

    "스마트폰": ["a modern smartphone", "holding a phone", "mobile device screen", "smartphone", "phone"],
    "컴퓨터": ["laptop computer on a desk", "desktop computer setup", "keyboard and mouse", "laptop", "computer"],
    "카메라": ["camera equipment", "photography gear", "camera lens and tripod", "camera", "photography"],
    "음향기기": ["headphones and speakers", "gaming console", "home theater system", "headphones", "audio"],
    "스마트웨어러블": ["smartwatch on a wrist", "fitness tracker", "wearable tech", "smartwatch", "wearable"],

    "실내환경": ["cozy living room interior", "home furniture design", "modern apartment interior", "living room", "interior"],
    "주방과 식사": ["kitchen interior appliances", "cooking in the kitchen", "dining table setup", "kitchen", "dining"],
    "침실": ["comfortable bedroom", "bed and pillows", "cozy home space", "bedroom", "bed"],
    "도시건축": ["modern city architecture", "skyscraper building", "street view of buildings", "architecture", "building"],
    "홈데코": ["home decor items", "wall paintings or decorations", "vases and home accents", "decor", "home decoration"],

    "요리": ["gourmet meal on a plate", "restaurant food", "fancy dish", "food", "meal"],
    "패스트푸드": ["fast food like burgers and fries", "street snacks", "casual dining", "fast food", "burger"],
    "과일과 채소": ["fresh fruits in a basket", "colorful vegetables", "healthy produce", "fruit", "vegetable"],
    "커피와 차": ["cup of coffee or tea", "cafe setting", "latte art", "coffee", "tea"],
    "디저트와 베이커리": ["cake and desserts", "freshly baked bread", "pastries", "dessert", "bakery"],

    "셀카": ["selfie of a person", "portrait close-up of face", "person smiling at camera", "selfie", "portrait"],
    "모임과 파티": ["group of friends posing", "people celebrating at a party", "group selfie", "party", "group"],
    "운동과 건강": ["gym workout scene", "running or jogging outdoors", "sports activities", "exercise", "fitness"],
    "패션": ["fashionable clothing outfit", "street style fashion", "accessories like shoes or bags", "fashion", "outfit"],
    "여행": ["traveling with luggage", "tourist visiting a landmark", "vacation vibes", "travel", "vacation"],

    "업무환경": ["professional office desk", "meeting room scene", "computer work environment", "office", "work"],
    "책과 문구": ["stack of books", "notebook with pen", "library bookshelves", "book", "stationery"],
    "교육과 공부": ["studying at a desk", "classroom setting", "academic lecture", "study", "education"],
    "문서와 영수증": ["printed business document", "receipt or invoice", "handwritten notes or paper", "document", "receipt"],
    "예술창작": ["painting on a canvas", "sketching or drawing", "creative craft project", "art", "painting"],

    "자동차": ["cars on the road", "traffic scene", "highway view", "car", "vehicle"],
    "대중교통": ["subway train station", "airplane or airport terminal", "bus stop", "transportation", "subway"],
    "기념일": ["birthday cake with candles", "christmas decorations", "holiday party", "celebration", "holiday"],
    "불꽃놀이": ["fireworks in the night sky", "colorful light show", "celebration event", "fireworks"],
    "종교와 문화": ["religious temple or church", "cultural ceremony", "traditional costume", "culture", "religion"],

    "야경": ["city night lights", "glowing street lamps", "night skyline", "night", "night view"],
    "추상미술": ["abstract patterns and colors", "artistic wallpaper", "geometric shapes", "abstract", "art"],
    "날씨": ["blue sky with clouds", "rainy day window view", "snowy weather", "weather", "sky"],
    "야외활동": ["camping tent in nature", "hiking in the mountains", "outdoor adventure", "outdoor", "camping"],
    "기타": ["miscellaneous objects", "random items", "unclassified image", "other", "misc"]
}

all_labels = [f"a photo of {desc}" for sublist in CATEGORY_MAP.values() for desc in sublist]
label_to_category = []
for cat, descs in CATEGORY_MAP.items():
    label_to_category.extend([cat] * len(descs))

@torch.no_grad()
def classify_content(file_path):
    image = Image.open(file_path).convert("RGB")
    inputs = processor(text=all_labels, images=image, return_tensors="pt", padding=True).to(device)
    outputs = model(**inputs)
    probs = outputs.logits_per_image.softmax(dim=1)

    top_prob, top_idx = probs.max(dim=1)
    if top_prob.item() < 0.15:
        return "其他"
    return label_to_category[top_idx.item()]

@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    results = []
    for file in files:
        file_path = os.path.join(IMAGES_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    
        category = classify_content(file_path)
        results.append({"category": category, "filename": file.filename})

    return {"images": results}

@app.delete("/delete")
async def delete_file(filepath: str):
    full_path = os.path.join(IMAGES_DIR, filepath)
    if os.path.exists(full_path):
        os.remove(full_path)
        return {"status": "success"}
    return {"status": "error", "message": "File not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)