from ultralytics import NAS

# Load a COCO-pretrained YOLO-NAS-s model
model = NAS("yolo_nas_l.pt")

# Display model information (optional)
model.info()

# Validate the model on the COCO8 example dataset
results = model.val(data="coco8.yaml")

# Run inference with the YOLO-NAS-s model on the 'test.png' image
results = model("test.png")

# Iterate over the results and save only images with detected objects
for result in results:
    # Check if any objects were detected (confidence > 0.5)
    if result.boxes.conf is not None and any(conf > 0.5 for conf in result.boxes.conf):
        result.save()  # Save image with detected objects
        print("Saved image with detected objects.")
    else:
        print("No objects detected with high confidence, not saving.")
    
print("Processing complete.")
