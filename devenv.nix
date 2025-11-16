{ config, pkgs, ... }:

{
  packages = with pkgs; [
    just
    semver-tool

    minio-client
    ffmpeg
  ];

  env = {
    GRANIAN_RELOAD_PATHS = "${config.git.root}/src";
  };

  languages = {
    python = {
      enable = true;

      uv.enable = true;
      venv.enable = true;
    };
  };
}
