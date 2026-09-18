"""Test đánh giá thị giác offline."""

import json
import os
import shutil

from delta_controller.camera_model import camera_model_from_gazebo_pose
from delta_controller.scene import OBJECTS, SIDE_CAMERA_GT_RPY, SIDE_CAMERA_GT_XYZ
from delta_controller.vision_eval import (
    bias,
    evaluate,
    load_dataset,
    perturb,
    Record,
    summarize,
)
import numpy as np
import pytest

K = np.array([[772.548, 0.0, 320.0], [0.0, 772.548, 240.0], [0.0, 0.0, 1.0]])
GT_CAMERA = camera_model_from_gazebo_pose(K, SIDE_CAMERA_GT_XYZ, SIDE_CAMERA_GT_RPY)
DATA = os.path.join(os.path.dirname(__file__), 'data')


def make_dataset(tmp_path):
    shutil.copy(os.path.join(DATA, 'side_camera_home.png'), tmp_path / 'home.png')
    truth = {o.name: [o.home_xy[0], o.home_xy[1], -0.205] for o in OBJECTS}
    labels = {'samples': [{'image': 'home.png', 'scenario': 'home', 'ground_truth': truth}]}
    (tmp_path / 'labels.json').write_text(json.dumps(labels))
    return load_dataset(str(tmp_path))


def test_real_frame_error_below_two_mm(tmp_path):
    records = evaluate(make_dataset(tmp_path), GT_CAMERA)
    assert {r.name for r in records} == {o.name for o in OBJECTS}
    stats = summarize(records)
    assert stats['detection_rate'] == 1.0
    assert stats['max_mm'] < 2.0


def test_heavy_darkening_loses_detections(tmp_path):
    records = evaluate(make_dataset(tmp_path), GT_CAMERA, brightness=0.1)
    assert summarize(records)['detection_rate'] < 1.0


def test_perturb_is_deterministic_and_clipped():
    img = np.full((10, 10, 3), 250, np.uint8)
    a = perturb(img, noise_sigma=20, brightness=1.2, seed=3)
    b = perturb(img, noise_sigma=20, brightness=1.2, seed=3)
    assert np.array_equal(a, b)
    assert a.max() <= 255 and a.min() >= 0
    assert np.array_equal(perturb(img), img)


def test_summarize_and_bias():
    recs = [Record('a', 's', 'red_box', (0.0, 0.0, 0.0), (0.003, 0.004, 0.0)),
            Record('b', 's', 'red_box', (0.0, 0.0, 0.0), (0.001, 0.0, 0.0)),
            Record('c', 's', 'red_box', (0.0, 0.0, 0.0), None)]
    stats = summarize(recs)
    assert stats['n'] == 3
    assert stats['detection_rate'] == pytest.approx(2 / 3)
    assert stats['mean_mm'] == pytest.approx(3.0)
    assert stats['max_mm'] == pytest.approx(5.0)
    assert bias(recs) == pytest.approx((2.0, 2.0))
