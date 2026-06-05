import gc
import time

import image
import lcd
import sensor
from maix import KPU


MODEL_PATH = "/sd/voc20_detect.kmodel"

LABELS = [
    "aeroplane",
    "bicycle",
    "bird",
    "boat",
    "bottle",
    "bus",
    "car",
    "cat",
    "chair",
    "cow",
    "diningtable",
    "dog",
    "horse",
    "motorbike",
    "person",
    "pottedplant",
    "sheep",
    "sofa",
    "train",
    "tvmonitor",
]

# These anchors must match the model. They are the common VOC20 YOLOv2 anchors
# shown in the CanMV KPU documentation for voc20_detect.kmodel.
ANCHORS = (
    1.3221,
    1.73145,
    3.19275,
    4.00944,
    5.05587,
    8.09892,
    9.47112,
    4.84053,
    11.2364,
    10.0071,
)


def main():
    lcd.init()
    lcd.clear(lcd.BLACK)

    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)
    sensor.skip_frames(time=1000)

    # The VOC20 model expects 320x256 input. Camera is 320x240, so copy it
    # into a 320x256 buffer before converting to AI format.
    od_img = image.Image(size=(320, 256))
    clock = time.clock()

    print("Loading K210 YOLO model:", MODEL_PATH)
    kpu = KPU()
    kpu.load_kmodel(MODEL_PATH)
    kpu.init_yolo2(
        ANCHORS,
        anchor_num=5,
        img_w=320,
        img_h=240,
        net_w=320,
        net_h=256,
        layer_w=10,
        layer_h=8,
        threshold=0.5,
        nms_value=0.2,
        classes=len(LABELS),
    )

    print("YOLO demo ready.")

    while True:
        gc.collect()
        clock.tick()

        img = sensor.snapshot()
        od_img.draw_image(img, 0, 0)
        od_img.pix_to_ai()
        kpu.run_with_output(od_img)
        detections = kpu.regionlayer_yolo2()

        if detections:
            for detection in detections:
                x, y, w, h, class_id, probability = detection
                label = LABELS[class_id] if class_id < len(LABELS) else str(class_id)
                img.draw_rectangle(x, y, w, h, color=(0, 255, 0))
                img.draw_string(x, y, "%s %.2f" % (label, probability), color=(255, 0, 0), scale=2)
                print(label, probability, x, y, w, h)

        img.draw_string(0, 0, "%2.1f fps" % clock.fps(), color=(0, 60, 255), scale=2)
        lcd.display(img)


main()
