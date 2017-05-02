# Flowfairy

This project aims to make it easier to create neural networks by magically creating the flow of data in the graph so you can focus more on creating the neural networks and less on how the data enters the graph. 

This is done by making it possible to specify what data should be collected and then doing all the boring stuff, rather than what and how the data should be sent through the graph.

-------------------------------------------------------------------------------

To run the network, simply `cd` to a folder (or subfolder) that contains a `settings.py` for your network, and 
execute `fairy run`.

Some of the files, such as `stages.py` are asumed to be in the same folder as `settings.py` and are imported 
automatically.

See the examples to get a feel for how the framework is set up.
