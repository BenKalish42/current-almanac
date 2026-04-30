const path = require("path");

const currentRepository = process.env.GITHUB_REPOSITORY || "owner/current-almanac";
const [owner, name] = currentRepository.split("/");

module.exports = {
  packagerConfig: {
    asar: true,
    appBundleId: "com.current.almanac.desktop",
    appCategoryType: "public.app-category.lifestyle",
    executableName: "current-almanac",
  },
  rebuildConfig: {},
  makers: [
    {
      name: "@electron-forge/maker-squirrel",
      config: {
        name: "current_almanac",
        setupExe: "CurrentAlmanacSetup.exe",
      },
    },
    {
      name: "@electron-forge/maker-zip",
      platforms: ["darwin"],
    },
    {
      name: "@electron-forge/maker-dmg",
      platforms: ["darwin"],
      config: {
        name: "Current Almanac",
      },
    },
    {
      name: "@electron-forge/maker-deb",
      config: {
        options: {
          name: "current-almanac",
          productName: "Current Almanac",
          maintainer: "Current Almanac",
          homepage: "https://current-almanac.netlify.app",
          categories: ["Utility", "Education"],
        },
      },
    },
    {
      name: "@electron-forge/maker-rpm",
      config: {
        options: {
          name: "current-almanac",
          productName: "Current Almanac",
          homepage: "https://current-almanac.netlify.app",
          categories: ["Utility", "Education"],
        },
      },
    },
  ],
  plugins: [
    {
      name: "@electron-forge/plugin-auto-unpack-natives",
      config: {},
    },
  ],
  publishers: [
    {
      name: "@electron-forge/publisher-github",
      config: {
        repository: {
          owner,
          name,
        },
        draft: true,
        prerelease: true,
      },
    },
  ],
  hooks: {
    packageAfterCopy: async (_config, buildPath) => {
      const source = path.join(process.cwd(), "dist");
      const destination = path.join(buildPath, "dist");
      await require("fs/promises").cp(source, destination, { recursive: true });
    },
  },
};
