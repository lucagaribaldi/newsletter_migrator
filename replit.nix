{ pkgs }: {
  deps = [
    pkgs.python310
    pkgs.python310Packages.pip
    pkgs.python310Packages.virtualenv
    pkgs.python310Packages.wheel
    pkgs.python310Packages.setuptools
  ];
  env = {
    PYTHONBIN = "${pkgs.python310}/bin/python3.10";
    LANG = "en_US.UTF-8";
    PYTHONUNBUFFERED = "1";
    REPLIT_POETRY_PYPI_REPOSITORY = "https://package-proxy.replit.com/pypi/";
    PIP_FIND_LINKS = "https://package-proxy.replit.com/pypi/simple/";
  };
}
