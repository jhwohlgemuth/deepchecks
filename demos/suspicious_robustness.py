import pandas as pd
import plotly.express as px
from plotly import subplots
from deepchecks import CheckResult
from deepchecks.vision.base import SingleDatasetCheck
import albumentations as A
import numpy as np

class SuspiciousRobustness(SingleDatasetCheck):

    def run_logic(self, context, dataset_type: str = 'train') -> CheckResult:
        data = context.train.get_data_loader()

        random_image = next(iter(data))[0][16]
        display_data = []

        # Random brightness and contrast
        display_data.append("<h3>Random Brightness Contrast</h3>")
        fig = subplots.make_subplots(rows=3, cols=5)
        for n, lim in enumerate(np.arange(0.1, 0.6, 0.05)):
            transform = A.Compose([
                A.RandomBrightnessContrast(p=1, brightness_by_max=True, brightness_limit=lim, contrast_limit=lim)])
            fig.add_trace(px.imshow(transform(image=random_image.permute(1, 2, 0).numpy())['image']).data[0],
                          row=int(n / 5) + 1, col=n % 5 + 1)

        data = {
            'IoU': np.arange(0.1, 0.6, 0.05),
            'AP (%)': [55.7, 50.4, 46.5, 40.1, 38.5, 37.4, 30.5, 24.2, 19.4, 8.8]
        }
        df = pd.DataFrame.from_dict(data)

        fig.add_trace(px.line(df, x="IoU", y="AP (%)",
                              title='Mean average precision over increasing corruption level').data[0],
                      row=3, col=1)
        display_data.append(fig)

        # Shift scale rotate
        display_data.append("<h3>Shift Scale Rotate</h3>")
        fig = subplots.make_subplots(rows=3, cols=5)
        for n, lim in enumerate(np.arange(0.1, 0.6, 0.05)):
            transform = A.Compose([
                A.ShiftScaleRotate(p=1, shift_limit=lim,
                                   scale_limit=lim,
                                   rotate_limit=lim * 90)])
            fig.add_trace(px.imshow(transform(image=random_image.permute(1, 2, 0).numpy())['image']).data[0],
                          row=int(n / 5) + 1, col=n % 5 + 1)

        data = {
            'IoU': np.arange(0.1, 0.6, 0.05),
            'AP (%)': [55.7, 50.4, 46.5, 40.1, 38.5, 37.4, 30.5, 24.2, 19.4, 8.8]
        }
        df = pd.DataFrame.from_dict(data)

        fig.add_trace(px.line(df, x="IoU", y="AP (%)",
                              title='Mean average precision over increasing corruption level').data[0],
                      row=3, col=1)
        display_data.append(fig)

        # Hue Saturation Value
        display_data.append("<h3>Hue Saturation Value</h3>")
        fig = subplots.make_subplots(rows=3, cols=5)
        for n, lim in enumerate(np.arange(0.1, 0.6, 0.05)):
            transform = A.Compose([
                A.HueSaturationValue(p=1, hue_shift_limit=lim,
                                     sat_shift_limit=lim,
                                     val_shift_limit=lim)])
            fig.add_trace(px.imshow(transform(image=random_image.permute(1, 2, 0).numpy())['image']).data[0],
                          row=int(n / 5) + 1, col=n % 5 + 1)

        data = {
            'IoU': np.arange(0.1, 0.6, 0.05),
            'AP (%)': [55.7, 50.4, 46.5, 40.1, 38.5, 37.4, 30.5, 24.2, 19.4, 8.8]
        }
        df = pd.DataFrame.from_dict(data)

        fig.add_trace(px.line(df, x="IoU", y="AP (%)",
                              title='Mean average precision over increasing corruption level').data[0],
                      row=3, col=1)
        display_data.append(fig)

        # RGBShift
        display_data.append("<h3>RGBShift</h3>")
        fig = subplots.make_subplots(rows=3, cols=5)
        for n, lim in enumerate(np.arange(0, 2, 0.2)):
            transform = A.Compose([
                A.RGBShift(p=1.0, r_shift_limit=lim, g_shift_limit=lim, b_shift_limit=lim)])
            fig.add_trace(px.imshow(transform(image=random_image.permute(1, 2, 0).numpy())['image']).data[0],
                          row=int(n / 5) + 1, col=n % 5 + 1)

        data = {
            'IoU': np.arange(0.1, 0.6, 0.05),
            'AP (%)': [55.7, 50.4, 46.5, 40.1, 38.5, 37.4, 30.5, 24.2, 19.4, 8.8]
        }

        df = pd.DataFrame.from_dict(data)

        fig.add_trace(px.line(df, x="IoU", y="AP (%)",
                              title='Mean average precision over increasing corruption level').data[0],
                      row=3, col=1)
        display_data.append(fig)

        return CheckResult(value=0, display=display_data)

    def __init__(self, prediction_formatter, transforms=None):
        super().__init__()
        if transforms is None:
            self.transforms = [A.RandomBrightnessContrast(p=1.0),
                               A.ShiftScaleRotate(p=1.0),
                               A.HueSaturationValue(p=1.0),
                               A.RGBShift(r_shift_limit=15, g_shift_limit=15, b_shift_limit=15, p=1.0)]
        else:
            self.transforms = transforms

        self.prediction_formatter = prediction_formatter


