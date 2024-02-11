# Azur Lane Painting Reconstruction

Builds sprites from the jumbled Texture2Ds and Meshes available in `Android/data/com.YoStarEN.AzurLane/files/AssetBundles/painting`. Can also extract facial expressions from `paintingface` and can sometimes paste them properly on those sprites.

Inspired by [Scighost/AzurLane-Painting-Tool](https://github.com/Scighost/AzurLane-Painting-Tool/blob/6d6301257a558d9dbde4a65e4cf25650fca797c8/AzurLane-Painting-Tool/PaintingInfo.cs#L260) which made it look easy enough.

~~Not gonna continue this because better tools (like [nobbyfix's](https://gist.github.com/nobbyfix/fb535462acc897ab1f39e5e9981e4645)) already exist and because I don't want to put the effort into figuring out the more complex sprites (like Arbiter: The Tower XIV, whose background is scaled differently) or edge cases (like `z46_2_tex`, which has no texture) or proper face placement.~~

usage:

```python
### this script ###
# outputs to output2 folder
python -m main2
python -m main2 -p "jiahe_3"

### nobbyfix's script ###
# outputs to root folder
python -m painting_reconstruct -d "input" -p "jiahe_3"
```

will update readme soon
