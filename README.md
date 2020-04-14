## Automatically Code Suggestion by Neural Network

A LSTM based method to complete the code by given chars/tokens.


### Train Model

install the requirement (python 3.5)

```bash
$ pip install -r requirements.txt
```

backend

```bash
$ cd ./lstm4backend
```

train token model

```bash
$ python train.py <model_name> token
```

train char model

```bash
$ python train.py <model_name> char
```

Note: dataset should be set inside the `train.py`. 
