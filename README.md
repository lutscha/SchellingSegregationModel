# SchellingSegregationModel
Evolving out of a single problem for the MIT Networks (14.15 / 6.3260) class, I created a variety of Shelling segregation model simulations. Below is a quick explanation of the model, the motivation for the different assignment algorithms, and some of the usage details.
## The model
We begin with a $n\times n$ board, the grid cells, from here on out referred to as **nodes**, are color either red or blue. Some fraction of the Nodes are left empty, we will also refer to these as white nodes. The nodes keep a count of their immediate neighbors, which are defined as the 8 nodes surrounding it (this means that grids that share a single vertex are still neighbors). They look at what fraction of their neighbors are of the same color as they are, this is defined as the node's $pval$. We have some value, $pbound\in[0,1]$, and if a node's $pval < pbound$, then it is *unsatisfied*.

Unsatisfied nodes move to empty cells(*). This continues until we either hit an iterations limit, or there are no more unsatisfied nodes. (**)

![](https://raw.githubusercontent.com/lutscha/ShellingSegregationModel/main/assets/example_assignment.gif)

(*) This is ambiguous, in what way are they moved? One assumption would be to move it to a random node. Another would be to move it to the closest satisfying node. One may move all unsatisfied nodes in bulk, only afterwards scanning for new unsatisfied nodes. Additionally, what if we move nodes only to satisfied squares, then (**) might be a problem as well, since we might not have any available satisfying empty squares. Imagine a high value of $pbound$, fore example $pbound=1$, then as long as the empty cell has two different colored neighbors, nobody will move there. This brings us to our next section.
## The assignment algorithms
When we decide to move a node, we can select the empty square in different methods, here we consider two main methods. We either take a random empty square, or we take the closest square, in terms of the standard Euclidean metric. These are the `random` and `closest` selection methods. As we mentioned above, we can also filter to only select satisfying nodes. This is the `satisfy` filter. If we decide to consider only satisfying nodes, we must decide what to do in case we hit a dead end. We can stop the simulation, or we can continue in some fashion, and here we continue by selecting a random or the closest node, depending on the selection method, even if does not satisfy the $pbound$ requirement. Giving the 'stop' and 'continue' flags as well.

Finally, we point out one more possibility. For example, in [Frank McCown's](http://nifty.stanford.edu/2014/mccown-schelling-model-segregation/) of Harding Universities implementation, it is outlined that the unsatisfied nodes are moved ***all at once***. This means that the set of unsatisfied nodes is assigned to new positions, along one of the assignment methods we mentioned above, and only then is the set updated. An alternative is updating after moving each node, which we denote by the flag `single`. 

The other method, where we reassign each batch has leaves one more ambiguity. Namely, assume we have nodes $A_1$ and $A_2$ to be reassigned. Assume we move $A_1$ to an empty square, now, the location where $A_1$ used to be is empty, but as we reassign $A_2$, is the board updated to count that location as empty? In other words, even though we update the set of unsatisfied nodes after each batch, do we update the set of empty nodes after each single node moved? If we do, we denote this by `whitebatch`, and if we don't, ie. the batch update might stop because we ran out of empty white nodes (even though they exist, they are only not updated yet), we call this plain `batch`.

This leaves us with a total of $18$ algorithms. We decide whether to run `single`,`whitebatch` or `batch` updates. Then for each of those, we decide if we are running `random` or `closest` selection. Then, each of these has three parameters, we could do any node, we could do only satisfying with stopping, or we could to only satisfying with continuing. Therefore we have $3\cdot 2\cdot 3=18$ algorithms.

## Usage

The main structure of the game is the `Board` object. 
```
new_simulation = Board(size=50, whiteP=0.1, redP=0.5, pbound=0.6, stopping = 1)
new_simulation.run(100, "batchRandom")
new_simulation.animate()
```

![](https://raw.githubusercontent.com/lutscha/ShellingSegregationModel/main/assets/batchRandom_example.gif)

The `size` parameter defines the length of an edge of the square, `whiteP` defines the percentage of empty nodes, `redP` determines what percentage of the ***remaining*** $(1-whiteP)$ nodes are red, the remainder being blue. The segregation parameter is `pbound`, and in some simulations running the `closest` selection, the algorithm gets stuck in a cycle. Therefore we implement the `stopping` parameter, if the number of unsatisfied nodes goes below the `stopping` parameter, the simulation stops. It is an optional argument with a default value of $1$.

The `board` object has some methods. As above, `run` runs the board with the specified algorithm. The algorithm dictionary keys are below.
```
        algoDict = {"singleRandom":self.step_single_random,
                        "singleClosest":self.step_single_closest,
                        "singleRandomSatisfyStop":self.step_single_randomSat_stop,
                        "singleRandomSatisfyContinue":self.step_single_randomSat_cont,
                        "singleClosestSatisfyStop":self.step_single_closestSat_stop,
                        "singleClosestSatisfyContinue":self.step_single_closestSat_cont,
                        "whitebatchRandom":self.step_whitebatch_random,
                        "batchRandom":self.step_batch_random,
                        "whitebatchRandomSatisfyStop":self.step_whitebatch_randomSat_stop,
                        "batchRandomSatisfyStop":self.step_batch_randomSat_stop,
                        "whitebatchRandomSatisfyContinue":self.step_whitebatch_randomSat_cont,
                        "batchRandomSatisfyContinue":self.step_batch_randomSat_cont,
                        "whitebatchClosest":self.step_whitebatch_closest,
                        "batchClosest":self.step_batch_closest,
                        "whitebatchClosestSatisfyStop":self.step_whitebatch_closestSat_stop,
                        "batchClosestSatisfyStop":self.step_batch_closestSat_stop,
                        "whitebatchClosestSatisfyContinue":self.step_whitebatch_closestSat_cont,
                        "batchClosestSatisfyContinue":self.step_batch_closestSat_cont}
```
Hopefully it is self-explanatory which key corresponds to which selection. Outside of the algorithm parameter, `run` also comes with the number of maximum iterations, which is $100$ in the example above.

The ending value of the board can be exported to a numpy array where red, white and blue are encoded as $100$, $0$ and $-100$ respectively, using `board.to_np_colorcode`. This is useful for visualizations, in fact the `animate` method uses this. There is also `board.to_np_pvals` returning a $2D$ numpy array of each nodes $pval$. Finally, `averagepval` returns the average $pval$ of all the non-empty nodes in the board.

There are some remnants of early implementation ideas, such as the unused method of the `Node` object, `color_and_update`, most of these come from an idea to optimize by updating only the neighbors of each node when doing `single` updating in the algorithm, but I scrapped it cause it didn't speed up smaller boards too drastically and was annoying to work with. Although it definitely remains as a possible optimization.

$$\begin{align}
\textit{"Premature optimization is the root of all evil."}& \\
& \text{- Donald Knuth}
\end{align}$$

I hope this is useful or interesting. Enjoy! :)
