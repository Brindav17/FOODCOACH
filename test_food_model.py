from clarifai.client.model import Model

# Your personal access token
PAT = "5509618baed64038b6b697351e7f1517"

# Initialize the Food Model
model = Model(
    url="https://clarifai.com/clarifai/main/models/food-item-recognition",
    pat=PAT
)

# Path to your image
image_path = r"D:\foodcoach\static\images\pizza.jpg"

# Predict
result = model.predict_by_filepath(image_path)

# Print predictions
for concept in result.outputs[0].data.concepts:
    print(f"{concept.name}: {concept.value:.2f}")
