#include <iostream>
#include <string>
#include <algorithm>

#include "genie/dat/DatFile.h"

int main(int argc, char *argv[])
{
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <path-to-AoE2DE-game-dir>" << std::endl;
        return 1;
    }

    std::string gameDir = argv[1];
    std::string datPath = gameDir + "/resources/_common/dat/empires2_x2_p1.dat";

    std::cout << "Loading: " << datPath << std::endl;

    genie::DatFile df;
    df.setGameVersion(genie::GV_LatestDE2);

    try {
        df.load(datPath.c_str());
    } catch (const std::exception &e) {
        std::cerr << "Failed to load dat file: " << e.what() << std::endl;
        return 1;
    }

    std::cout << "File version: " << df.FileVersion << std::endl;
    std::cout << std::endl;

    // Civilizations
    std::cout << "=== Civilizations (" << df.Civs.size() << ") ===" << std::endl;
    for (size_t i = 0; i < df.Civs.size(); i++) {
        std::cout << "  [" << i << "] " << df.Civs[i].Name << std::endl;
    }
    std::cout << std::endl;

    // Technologies
    std::cout << "=== Technologies (" << df.Techs.size() << ") ===" << std::endl;
    size_t techLimit = std::min<size_t>(df.Techs.size(), 10);
    for (size_t i = 0; i < techLimit; i++) {
        if (!df.Techs[i].Name.empty()) {
            std::cout << "  [" << i << "] " << df.Techs[i].Name << std::endl;
        }
    }
    if (df.Techs.size() > techLimit)
        std::cout << "  ... and " << (df.Techs.size() - techLimit) << " more" << std::endl;
    std::cout << std::endl;

    // Units from Gaia (civ 0)
    if (!df.Civs.empty()) {
        const auto &gaia = df.Civs[0];
        std::cout << "=== Units in " << gaia.Name << " (" << gaia.Units.size() << ") ===" << std::endl;
        size_t printed = 0;
        for (size_t i = 0; i < gaia.Units.size() && printed < 10; i++) {
            const auto &unit = gaia.Units[i];
            if (!unit.Name.empty()) {
                std::cout << "  [" << unit.ID << "] " << unit.Name
                          << " (HP: " << unit.HitPoints << ")" << std::endl;
                printed++;
            }
        }
        if (gaia.Units.size() > printed)
            std::cout << "  ... and " << (gaia.Units.size() - printed) << " more" << std::endl;
    }
    std::cout << std::endl;

    // Summary counts
    std::cout << "=== Summary ===" << std::endl;
    std::cout << "  Graphics: " << df.Graphics.size() << std::endl;
    std::cout << "  Sounds:   " << df.Sounds.size() << std::endl;
    std::cout << "  Effects:  " << df.Effects.size() << std::endl;

    return 0;
}
