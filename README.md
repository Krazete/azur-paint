# Azur Lane Painting Reconstruction

> Note: The 2024-05-16 update messed everything up. Single-layer sprites seem okay, but multi-layer sprites' positioning is all wrong. Idk how soon I'll be able to fix it.

Builds sprites from the jumbled Texture2Ds and Meshes available in the `AssetBundles/painting` folder. Also requires the `AssetBundles/dependencies` file. These are both located within `Android/data/com.YoStarEN.AzurLane/files`.

This repo was inspired by:

* [AzurLane-Painting-Tool](https://github.com/Scighost/AzurLane-Painting-Tool/blob/6d6301257a558d9dbde4a65e4cf25650fca797c8/AzurLane-Painting-Tool/PaintingInfo.cs#L260) by [Scighost](https://github.com/Scighost)
* [painting_reconstruct.py](https://gist.github.com/nobbyfix/fb535462acc897ab1f39e5e9981e4645) by [nobbyfix](https://github.com/nobbyfix)

~~My `main2.py` script is more accurate by considering the mesh's `m_LocalAABB` property and its `m_Center` and `m_Extent` values. These values indicate the location of each sprite piece relative to their bounding box.~~ (not anymore, see note up top)

## Usage

### main.py

```py
python -m main -p ankeleiqi
python -m main -p ankeleiqi_jz1
python -m main -p ankeleiqi_jz2
python -m main -p ankeleiqi_rw
python -m main -p ankeleiqi_tx3
```

* outputs to `output` folder
* unlike the two scripts below, the `-p` input is the name of `_tex` files minus the `_tex` (instead of the assetbundle file)
* process one layer, not an entire sprite
* doesn't consider positioning and scaling info of sprite layers

### main2.py

```py
python -m main2 -p ankeleiqi
```

* outputs to `output2` folder

### nobbyfix's script

```py
python -m painting_reconstruct -d "input" -p ankeleiqi
```

* outputs to root folder
* must first replace lines 299-300 (the `asset_dir.name != "AssetBundles"` conditional) with `pass`