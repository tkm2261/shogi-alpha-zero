About
=====



Environment
-----------

* Python 3.6.3
* tensorflow-gpu: 1.3.0
* Keras: 2.0.8

### Supervised Learning

```bash
python src/shogi_zero/run.py sl
```

### Reinforcement Learning

This AlphaGo Zero implementation consists of three workers: `self`, `opt` and `eval`.

* `self` is Self-Play to generate training data by self-play using BestModel.
* `opt` is Trainer to train model, and generate next-generation models.
* `eval` is Evaluator to evaluate whether the next-generation model is better than BestModel. If better, replace BestModel.


Data
-----

* `data/model/model_best_*`: BestModel.
* `data/model/next_generation/*`: next-generation models.
* `data/play_data/play_*.json`: generated training data.
* `logs/main.log`: log file.

If you want to train the model from the beginning, delete the above directories.

How to use
==========

Setup
-------
### install libraries
```bash
pip install -r requirements.txt
```

If you want to use GPU, follow [these instructions](https://www.tensorflow.org/install/) to install with pip3.

Make sure Keras is using Tensorflow and you have Python 3.6.3+. Depending on your environment, you may have to run python3/pip3 instead of python/pip.


Basic Usage
------------

For training model, execute `Self-Play`, `Trainer` and `Evaluator`.

**Note**: Make sure you are running the scripts from the top-level directory of this repo, i.e. `python src/shogi_zero/run.py opt`, not `python run.py opt`.


Self-Play
--------

```bash
python src/shogi_zero/run.py self
```

When executed, Self-Play will start using BestModel.
If the BestModel does not exist, new random model will be created and become BestModel.

### options
* `--new`: create new BestModel
* `--type mini`: use mini config for testing, (see `src/shogi_zero/configs/mini.py`)

Trainer
-------

```bash
python src/shogi_zero/run.py opt
```

When executed, Training will start.
A base model will be loaded from latest saved next-generation model. If not existed, BestModel is used.
Trained model will be saved every epoch.

### options
* `--type mini`: use mini config for testing, (see `src/shogi_zero/configs/mini.py`)
* `--total-step`: specify total step(mini-batch) numbers. The total step affects learning rate of training.

Evaluator
---------

```bash
python src/shogi_zero/run.py eval
```

When executed, Evaluation will start.
It evaluates BestModel and the latest next-generation model by playing about 200 games.
If next-generation model wins, it becomes BestModel.

### options
* `--type mini`: use mini config for testing, (see `src/shogi_zero/configs/mini.py`)


Supervised Learning
---------
```bash
python src/shogi_zero/run.py sl
```
