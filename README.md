# Buy-or-Rent Decisions in a Two-Token Blockchain Network

This repository contains all code used for my AI Master's thesis: "Buy-or-Rent Decisions in a Two-Token Blockchain Network". The "Code" directory contains all the source code of the model. Files used to run and analyze the model can be found in the "Experiments" directory, split by the experiments outlined in the thesis. 

## Paper
### Abstract
Blockchain technology has seen an incredible surge in popularity in recent years, and many different blockchain networks exist at present. VeChainThor is a blockchain network that uses a two-token model in which the main token generates gas tokens, and the gas tokens are used to pay for network use. This two-token model yields what we call the VeChain Decision Problem: users of the network need to decide whether they want to buy gas tokens directly, or if they want to buy main tokens to generate the gas tokens. In the field of online algorithms, the Ski Rental Problem refers to a well-studied collection of problems in which one needs to decide between renting or buying. In this exploratory research, we map the VeChain Decision Problem to the Ski Rental Problem while exploring the features that make the VeChain Decision Problem unique and more challenging to solve. Most importantly, we identify and model the uniquely direct relationship between user decisions and buy/rent prices that order-driven cryptocurrency exchanges provide through their limit order books. We consider deterministic and randomized online algorithms that optimally solve Ski Rental Problems, and we analyze their performance in the VeChain Decision Problem. Moreover, we explore the influence of the usage of these algorithms on the network adoption ratio and -speed of network users. Results suggest that the consistency in performance of deterministic algorithms makes them more appropriate for use in the VeChain Decision Problem than randomized algorithms. Results also show that trends in the buy-to-rent price ratio influence user performance and adoption behavior. Finally, simulations in a multi-agent setting suggest that user performance is affected by the strategies applied by other users. Future studies are encouraged to advance multi-agent research of this problem, and to improve the existing deterministic algorithms by incorporating price predictions.

### Full version
The complete version of the thesis can be found in the file titled `thesis.pdf`. Alternatively, you can download it from the RUG RSE library [here](https://fse.studenttheses.ub.rug.nl/28826/).

## Requirements
The entire model is implemented using the [Mesa](https://mesa.readthedocs.io/en/latest/) framework (v. 0.9.0), on Python 3.9.7. A list of all required Python packages can be found in `requirements.txt`. The same file can be used to install them:

`$ pip install -r requirements.txt`
