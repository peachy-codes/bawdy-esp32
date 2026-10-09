package com.wled.sequencer;

import com.wled.sequencer.client.EngineClient;
import com.wled.sequencer.model.SequenceRepository;
import com.wled.sequencer.ui.MainWindow;
import com.wled.sequencer.universe.PatchTableModel;
import com.wled.sequencer.universe.SpatialUniverseModel;

import javax.swing.*;
import javax.swing.plaf.FontUIResource;
import java.awt.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Enumeration;

/**
 * Application entry point for the WLED Spatial Universe & Sequence Editor.
 * Configured with default Swing settings and Arial font throughout.
 */
public class Main {

    static {
        System.setProperty("awt.useSystemAAFontSettings", "on");
        System.setProperty("swing.aatext", "true");
        System.setProperty("apple.laf.useScreenMenuBar", "true");
        System.setProperty("apple.awt.application.name", "WLED Universe Manager");
    }

    public static void main(String[] args) {
        String engineUrl = "http://127.0.0.1:8765";
        Path sequencesDir = resolveSequencesDirectory();
        Path universePath = resolveUniversePath();
        Path patchPath = resolvePatchPath();

        for (int i = 0; i < args.length; i++) {
            if ("--engine".equals(args[i]) && i + 1 < args.length) {
                engineUrl = args[++i];
            } else if ("--sequences".equals(args[i]) && i + 1 < args.length) {
                sequencesDir = Path.of(args[++i]);
            } else if ("--universe".equals(args[i]) && i + 1 < args.length) {
                universePath = Path.of(args[++i]);
            } else if ("--patch".equals(args[i]) && i + 1 < args.length) {
                patchPath = Path.of(args[++i]);
            }
        }

        if (GraphicsEnvironment.isHeadless()) {
            System.err.println("Notice: Running in headless environment without display device.");
            return;
        }

        final String finalEngineUrl = engineUrl;
        final Path finalSequencesDir = sequencesDir;
        final Path finalUniversePath = universePath;
        final Path finalPatchPath = patchPath;

        SwingUtilities.invokeLater(() -> {
            applyDefaultSettingsWithArial();

            SequenceRepository repo = new SequenceRepository(finalSequencesDir);
            EngineClient client = new EngineClient(finalEngineUrl);

            SpatialUniverseModel universe = null;
            if (finalUniversePath != null && Files.exists(finalUniversePath)) {
                try {
                    universe = SpatialUniverseModel.loadFromFile(finalUniversePath);
                } catch (Exception e) {
                    System.err.println("Warning: Could not load universe file: " + e.getMessage());
                }
            }

            PatchTableModel patch = null;
            if (finalPatchPath != null && Files.exists(finalPatchPath)) {
                try {
                    patch = PatchTableModel.loadFromFile(finalPatchPath);
                } catch (Exception e) {
                    System.err.println("Warning: Could not load patch file: " + e.getMessage());
                }
            }

            MainWindow window = new MainWindow(repo, client, universe, patch);
            window.setVisible(true);
        });
    }

    private static void applyDefaultSettingsWithArial() {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {}

        Font arialPlain = new Font("Arial", Font.PLAIN, 12);
        FontUIResource fontResource = new FontUIResource(arialPlain);

        Enumeration<Object> keys = UIManager.getDefaults().keys();
        while (keys.hasMoreElements()) {
            Object key = keys.nextElement();
            Object value = UIManager.get(key);
            if (value instanceof Font) {
                Font f = (Font) value;
                UIManager.put(key, new FontUIResource("Arial", f.getStyle(), f.getSize()));
            } else if (key.toString().endsWith(".font")) {
                UIManager.put(key, fontResource);
            }
        }
    }

    private static Path resolveSequencesDirectory() {
        Path p1 = Path.of("sequences");
        if (Files.isDirectory(p1)) return p1.toAbsolutePath();

        Path p2 = Path.of("..", "sequences");
        if (Files.isDirectory(p2)) return p2.toAbsolutePath();

        return p1.toAbsolutePath();
    }

    private static Path resolveUniversePath() {
        Path p1 = Path.of("data", "venue", "universe.json");
        if (Files.exists(p1)) return p1.toAbsolutePath();

        Path p2 = Path.of("..", "data", "venue", "universe.json");
        if (Files.exists(p2)) return p2.toAbsolutePath();

        return p1.toAbsolutePath();
    }

    private static Path resolvePatchPath() {
        Path p1 = Path.of("data", "venue", "patch.json");
        if (Files.exists(p1)) return p1.toAbsolutePath();

        Path p2 = Path.of("..", "data", "venue", "patch.json");
        if (Files.exists(p2)) return p2.toAbsolutePath();

        return p1.toAbsolutePath();
    }
}
