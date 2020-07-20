Run 

```
export GRAPHML='<MY GRAPHML>'
export XNETPATH='/tmp/map.xnet'
export ACCESSIBS='/tmp/accessibs.txt'

python graphml2xnet.py --graphml $GRAPHML --output $XNETPATH
Build_Linux/CVAccessibility -l 3 $XNETPATH $ACCESSIBS
python plot_accessibs.py --graphml $GRAPHML --accessibs $ACCESSIBS

python weight_graph.py --accessibs $ACCESSIBS --xnet $XNETPATH --outpath $WXNETPATH
``` 

