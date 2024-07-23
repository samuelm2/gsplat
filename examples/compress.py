import torch
import numpy as np
import imageio
import os
from utils import sh_to_rgb
import imagecodecs
from tqdm import tqdm


def compress_means(grid, compress_dir):
    # Clamp to 1st and 99th percentile
    for i in range(grid.shape[-1]):
        grid[i] = torch.clamp(
            grid[i], torch.quantile(grid[i], 0.01), torch.quantile(grid[i], 0.99)
        )

    grid_mins = torch.amin(grid, dim=(0, 1))
    grid_maxs = torch.amax(grid, dim=(0, 1))
    grid_norm = (grid - grid_mins) / (grid_maxs - grid_mins)

    img_norm = grid_norm.detach().cpu().numpy()
    np.savez_compressed(os.path.join(compress_dir, "means.npz"), img_norm)


def compress_scales(grid, compress_dir):
    grid_mins = torch.amin(grid, dim=(0, 1))
    grid_maxs = torch.amax(grid, dim=(0, 1))
    grid_norm = (grid - grid_mins) / (grid_maxs - grid_mins)

    img_norm = grid_norm.detach().cpu().numpy()
    img = (img_norm * 255).astype(np.uint8)
    imageio.imwrite(os.path.join(compress_dir, "scales.png"), img)


def compress_sh0(grid, compress_dir):
    grid = grid.squeeze()
    grid_mins = torch.amin(grid, dim=(0, 1))
    grid_maxs = torch.amax(grid, dim=(0, 1))
    grid_norm = (grid - grid_mins) / (grid_maxs - grid_mins)

    img_norm = grid_norm.detach().cpu().numpy()
    img = (img_norm * 255).astype(np.uint8)
    imageio.imwrite(os.path.join(compress_dir, "sh0.png"), img)


def compress_quats(grid, compress_dir):
    # grid = grid[..., :3]

    img_norm = grid.detach().cpu().numpy()
    img = (img_norm * 255).astype(np.uint8)
    imageio.imwrite(os.path.join(compress_dir, "quats.png"), img)


def compress_opacities(grid, compress_dir):
    img_norm = grid.detach().cpu().numpy()
    img = (img_norm * 255).astype(np.uint8)
    imageio.imwrite(os.path.join(compress_dir, "opacities.png"), img)


def compress_splats(splats, compress_dir):
    n_gs = len(splats["means"])
    n_sidelen = int(n_gs**0.5)
    attr_names = ["means", "scales", "sh0", "quats", "opacities"]
    for attr_name in attr_names:
        compress_fn = eval(f"compress_{attr_name}")
        param = splats[attr_name]
        grid = param.reshape(n_sidelen, n_sidelen, *param.shape[1:])
        compress_fn(grid, compress_dir)

    # splats_keys = ["means", "scales", "sh0", "quats", "opacities"]
    # params = torch.cat([splats[k].reshape(n_gs, -1) for k in splats_keys], dim=-1)
    # grid = params.reshape((n_sidelen, n_sidelen, -1))

    # grid_mins = torch.amin(grid, dim=(0, 1))
    # grid_maxs = torch.amax(grid, dim=(0, 1))
    # grid_norm = (grid - grid_mins) / (grid_maxs - grid_mins)

    # grid_norm = grid_norm.detach().cpu().numpy()
    # for i in range(0, grid_norm.shape[-1], 3):
    #     img = (grid_norm[..., i : i + 3] * 255).astype(np.uint8)
    #     if img.shape[-1] != 3:
    #         img = np.concatenate(
    #             [img, np.zeros((img.shape[0], img.shape[1], 1), dtype=np.uint8)],
    #             axis=-1,
    #         )
    #     # imageio.imwrite(os.path.join(compress_dir, f"img_{i}.png"), img)
    #     imageio.imwrite(os.path.join(compress_dir, f"img_{i}.jpg"), img)


def decompress_splats(compress_dir):
    imgs = []
    for i in range(0, 14, 3):
        img = imageio.imread(os.path.join(compress_dir, f"img_{i}.jpg"))
        imgs.append(img)
    grid_norm = np.concatenate(imgs, axis=2)[..., :14]
    print(grid_norm.shape)


def main():
    device = "cuda:0"
    ckpt_path = "examples/results/360_v2/3dgs_sh0_sort/bicycle/ckpts/ckpt_29999.pt"
    out_dir = "examples/results/compress"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    ckpt = torch.load(ckpt_path, map_location=device)
    # torch.save({"splats": ckpt["splats"]}, os.path.join(out_dir, "splats.pt"))
    compress_splats(ckpt["splats"], out_dir)

    # decompress_splats(out_dir)

    # splats = ckpt["splats"]
    # n_gs = len(splats["means"])
    # n_sidelen = int(n_gs**0.5)
    # params = torch.cat([splats[k].reshape(n_gs, -1) for k in splats.keys()], dim=-1)
    # grid = params.reshape((n_sidelen, n_sidelen, -1))
    # grid_rgb = sh_to_rgb(grid[:, :, -3:])
    # grid_rgb = torch.clamp(grid_rgb, 0.0, 1.0)
    # grid_rgb = grid_rgb.detach().cpu().numpy()
    # grid_rgb = (grid_rgb * 255).astype(np.uint8)
    # imageio.imwrite(os.path.join(out_dir, "rgb.png"), grid_rgb)
    # imageio.imwrite(os.path.join(out_dir, "rgb.jpg"), grid_rgb)
    # imagecodecs.imwrite(os.path.join(out_dir, "rgb.jxl"), grid_rgb)


# def gif():
#     scenes = ["garden", "bicycle", "stump", "treehill", "flowers", "bonsai"]
#     for scene in tqdm(scenes):
#         ckpt_dir = f"examples/results/360_v2/3dgs_sh0_sort/{scene}/ckpts"

#         writer = imageio.get_writer(f"{ckpt_dir}/{scene}_mcmc_grid.mp4", fps=10)

#         for step in range(500, 30000, 100):
#             grid = imageio.imread(os.path.join(ckpt_dir, f"grid_step{step:04d}.png"))
#             if grid.shape[0] != 0:
#                 img = np.zeros((1000, 1000, 3), dtype=np.uint8)
#                 img[: grid.shape[0], : grid.shape[1], :] = grid
#             else:
#                 img = grid

#             writer.append_data(img)
#         writer.close()


if __name__ == "__main__":
    main()
    # gif()