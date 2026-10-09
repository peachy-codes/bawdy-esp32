package com.wled.sequencer.ui.canvas;

import com.wled.sequencer.model.SequenceStep;
import com.wled.sequencer.player.TimelinePlayer;
import com.wled.sequencer.universe.BoundingBox3D;
import com.wled.sequencer.universe.FixtureModel;
import com.wled.sequencer.universe.PatchSegmentModel;
import com.wled.sequencer.universe.PatchTableModel;
import com.wled.sequencer.universe.Point3D;
import com.wled.sequencer.universe.SpatialUniverseModel;

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.awt.geom.*;
import java.util.*;
import java.util.List;
import java.util.function.Consumer;

/**
 * High-performance Java 2D Spatial Stage Canvas rendering the complete venue blueprint,
 * 28 physical/virtual fixtures, 5,153 individual LED diodes, catenary bulb curves,
 * 2D matrix panels, floor lamp diffusion pools, and real-time lighting simulation.
 */
public class StageCanvasPanel extends JPanel {
    private static final Font FONT_ARIAL_PLAIN_10 = new Font("Arial", Font.PLAIN, 10);
    private static final Font FONT_ARIAL_PLAIN_11 = new Font("Arial", Font.PLAIN, 11);
    private static final Font FONT_ARIAL_BOLD_11 = new Font("Arial", Font.BOLD, 11);
    private static final Font FONT_ARIAL_BOLD_12 = new Font("Arial", Font.BOLD, 12);

    private SpatialUniverseModel universe;
    private PatchTableModel patchTable;
    private TimelinePlayer player;

    // Viewport transform (World meters to Screen pixels)
    private double panX = 0.0;
    private double panY = 0.0;
    private double zoom = 42.0; // pixels per meter default
    private Point lastMousePos = null;

    // Selection & Hover
    private FixtureModel selectedFixture = null;
    private FixtureModel hoveredFixture = null;
    private Point lastHoverPoint = null;
    private Consumer<FixtureModel> onFixtureSelectedListener = null;

    // Toggles
    private boolean showGrid = true;
    private boolean showBlueprint = true;
    private boolean showLabels = true;
    private boolean showBeams = true;

    // Simulation Engine
    public enum SimulationMode {
        TIMELINE,
        ANGLE_SWEEP,
        RADIAL_PULSE,
        RAINBOW_CLOUD,
        LINEAR_GRADIENT,
        BLACKOUT
    }

    private SimulationMode simulationMode = SimulationMode.TIMELINE;
    private javax.swing.Timer animationTimer;
    private double simTimeSec = 0.0;
    private long lastAnimTimestamp = 0;
    private double masterBrightness = 1.0;
    private double simulationSpeed = 1.0;

    // Cached colors for active simulation frame
    private final Map<String, List<Color>> fixtureColorCache = new HashMap<>();

    public StageCanvasPanel(SpatialUniverseModel universe, PatchTableModel patchTable, TimelinePlayer player) {
        this.universe = universe;
        this.patchTable = patchTable;
        this.player = player;

        setBackground(new Color(13, 17, 26)); // Deep Blueprint Dark Navy
        setFocusable(true);

        setupMouseControls();
        setupKeyControls();
        setupAnimationTimer();

        // Fit view after component is initially laid out
        addComponentListener(new ComponentAdapter() {
            private boolean firstResize = true;
            @Override
            public void componentResized(ComponentEvent e) {
                if (firstResize && getWidth() > 50 && getHeight() > 50) {
                    firstResize = false;
                    fitView();
                }
            }
        });
    }

    public void setUniverse(SpatialUniverseModel universe) {
        this.universe = universe;
        this.selectedFixture = null;
        this.hoveredFixture = null;
        fixtureColorCache.clear();
        fitView();
        repaint();
    }

    public void setPatchTable(PatchTableModel patchTable) {
        this.patchTable = patchTable;
        repaint();
    }

    public void setPlayer(TimelinePlayer player) {
        this.player = player;
        repaint();
    }

    public void setOnFixtureSelectedListener(Consumer<FixtureModel> listener) {
        this.onFixtureSelectedListener = listener;
    }

    public void setSelectedFixture(FixtureModel fixture) {
        this.selectedFixture = fixture;
        repaint();
    }

    public FixtureModel getSelectedFixture() {
        return selectedFixture;
    }

    public void setSimulationMode(SimulationMode mode) {
        this.simulationMode = mode;
        repaint();
    }

    public SimulationMode getSimulationMode() {
        return simulationMode;
    }

    public void blackout() {
        this.simulationMode = SimulationMode.BLACKOUT;
        for (List<Color> cols : fixtureColorCache.values()) {
            java.util.Collections.fill(cols, Color.BLACK);
        }
        repaint();
    }

    public void resetTimeline() {
        this.simulationMode = SimulationMode.TIMELINE;
        this.simTimeSec = 0.0;
        for (List<Color> cols : fixtureColorCache.values()) {
            java.util.Collections.fill(cols, Color.BLACK);
        }
        repaint();
    }

    public void setMasterBrightness(double brightness) {
        this.masterBrightness = Math.max(0.0, Math.min(1.0, brightness));
        repaint();
    }

    public void setSimulationSpeed(double speed) {
        this.simulationSpeed = Math.max(0.1, speed);
    }

    public void toggleGrid() {
        this.showGrid = !this.showGrid;
        repaint();
    }

    public void toggleBlueprint() {
        this.showBlueprint = !this.showBlueprint;
        repaint();
    }

    public void toggleLabels() {
        this.showLabels = !this.showLabels;
        repaint();
    }

    public void toggleBeams() {
        this.showBeams = !this.showBeams;
        repaint();
    }

    // --- Navigation & Camera Controls ---

    public void fitView() {
        if (universe == null || getWidth() <= 0 || getHeight() <= 0) return;
        BoundingBox3D bbox = universe.getBoundingBox();
        if (bbox == null) return;

        double venueW = bbox.getWidth();
        double venueH = bbox.getHeight();
        if (venueW <= 0) venueW = 14.0;
        if (venueH <= 0) venueH = 14.0;

        double availW = Math.max(100, getWidth() - 80);
        double availH = Math.max(100, getHeight() - 80);

        this.zoom = Math.min(availW / venueW, availH / venueH);
        this.zoom = Math.max(12.0, Math.min(160.0, this.zoom));

        // Center on universe bounding box center
        double centerX = bbox.getCenterX();
        double centerY = bbox.getCenterY();

        this.panX = -centerX * zoom;
        this.panY = centerY * zoom; // inverted Y

        repaint();
    }

    public void resetZoom() {
        this.zoom = 42.0;
        this.panX = 0.0;
        this.panY = 0.0;
        repaint();
    }

    public void resetView() {
        resetZoom();
    }

    public void zoomIn() {
        adjustZoom(1.25, getWidth() / 2.0, getHeight() / 2.0);
    }

    public void zoomOut() {
        adjustZoom(0.8, getWidth() / 2.0, getHeight() / 2.0);
    }

    private void adjustZoom(double factor, double pivotX, double pivotY) {
        double oldZoom = this.zoom;
        double newZoom = Math.max(10.0, Math.min(250.0, oldZoom * factor));
        if (Math.abs(newZoom - oldZoom) < 0.001) return;

        // Keep point under pivot stationary
        double worldPivotX = (pivotX - (getWidth() / 2.0 + panX)) / oldZoom;
        double worldPivotY = ((getHeight() / 2.0 + panY) - pivotY) / oldZoom;

        this.zoom = newZoom;
        this.panX = pivotX - (getWidth() / 2.0) - (worldPivotX * newZoom);
        this.panY = pivotY - (getHeight() / 2.0) + (worldPivotY * newZoom);

        repaint();
    }

    // --- World <-> Screen Coordinate Transformations ---

    private double worldToScreenX(double wx) {
        return (getWidth() / 2.0) + panX + (wx * zoom);
    }

    private double worldToScreenY(double wy) {
        return (getHeight() / 2.0) + panY - (wy * zoom);
    }

    private double screenToWorldX(double sx) {
        return (sx - (getWidth() / 2.0 + panX)) / zoom;
    }

    private double screenToWorldY(double sy) {
        return ((getHeight() / 2.0 + panY) - sy) / zoom;
    }

    // --- Interactive Mouse & Key Controls ---

    private void setupMouseControls() {
        MouseAdapter ma = new MouseAdapter() {
            @Override
            public void mousePressed(MouseEvent e) {
                lastMousePos = e.getPoint();
                requestFocusInWindow();
            }

            @Override
            public void mouseReleased(MouseEvent e) {
                lastMousePos = null;
            }

            @Override
            public void mouseDragged(MouseEvent e) {
                if (lastMousePos != null) {
                    double dx = e.getX() - lastMousePos.getX();
                    double dy = e.getY() - lastMousePos.getY();
                    panX += dx;
                    panY += dy;
                    lastMousePos = e.getPoint();
                    repaint();
                }
            }

            @Override
            public void mouseWheelMoved(MouseWheelEvent e) {
                double factor = e.getPreciseWheelRotation() < 0 ? 1.15 : 0.87;
                adjustZoom(factor, e.getX(), e.getY());
            }

            @Override
            public void mouseMoved(MouseEvent e) {
                lastHoverPoint = e.getPoint();
                FixtureModel prevHover = hoveredFixture;
                hoveredFixture = findFixtureAt(e.getX(), e.getY());
                if (prevHover != hoveredFixture) {
                    repaint();
                }
            }

            @Override
            public void mouseClicked(MouseEvent e) {
                if (e.getClickCount() == 2) {
                    fitView();
                    return;
                }
                FixtureModel clicked = findFixtureAt(e.getX(), e.getY());
                selectedFixture = clicked;
                if (onFixtureSelectedListener != null) {
                    onFixtureSelectedListener.accept(clicked);
                }
                repaint();
            }
        };

        addMouseListener(ma);
        addMouseMotionListener(ma);
        addMouseWheelListener(ma);
    }

    private void setupKeyControls() {
        addKeyListener(new KeyAdapter() {
            @Override
            public void keyPressed(KeyEvent e) {
                if (e.getKeyCode() == KeyEvent.VK_F) {
                    fitView();
                } else if (e.getKeyCode() == KeyEvent.VK_0) {
                    resetZoom();
                } else if (e.getKeyCode() == KeyEvent.VK_G) {
                    toggleGrid();
                } else if (e.getKeyCode() == KeyEvent.VK_L) {
                    toggleLabels();
                }
            }
        });
    }

    private FixtureModel findFixtureAt(double sx, double sy) {
        if (universe == null) return null;
        double hitRadiusPixels = 16.0;

        for (FixtureModel f : universe.getFixtures()) {
            for (Point3D p : f.getPoints()) {
                double px = worldToScreenX(p.getX());
                double py = worldToScreenY(p.getY());
                if (Point2D.distance(sx, sy, px, py) <= hitRadiusPixels) {
                    return f;
                }
            }
        }
        return null;
    }

    // --- Animation & Simulation Loop ---

    private void setupAnimationTimer() {
        lastAnimTimestamp = System.nanoTime();
        animationTimer = new javax.swing.Timer(16, e -> { // ~60 FPS
            long now = System.nanoTime();
            double dt = (now - lastAnimTimestamp) / 1_000_000_000.0;
            lastAnimTimestamp = now;
            if (dt > 0.1) dt = 0.016;

            simTimeSec += dt * simulationSpeed;
            updateSimulationColors();
            repaint();
        });
        animationTimer.start();
    }

    private void updateSimulationColors() {
        if (universe == null) return;

        double t = simTimeSec;
        if (player != null && player.isPlaying()) {
            t = player.getElapsedSec();
        }

        for (FixtureModel f : universe.getFixtures()) {
            List<Color> colors = fixtureColorCache.computeIfAbsent(f.getId(), k -> new ArrayList<>());
            int count = f.getPoints().size();
            while (colors.size() < count) colors.add(Color.BLACK);

            for (int i = 0; i < count; i++) {
                Point3D p = f.getPoints().get(i);
                Color c = evaluatePixelColor(f, i, p, t);
                colors.set(i, c);
            }
        }
    }

    private Color evaluatePixelColor(FixtureModel f, int pixelIndex, Point3D p, double timeVal) {
        if (simulationMode == SimulationMode.BLACKOUT) {
            return Color.BLACK;
        }

        if (simulationMode == SimulationMode.ANGLE_SWEEP) {
            // 45 degree spatial travelling wave
            double coord = (p.getX() + p.getY()) * 0.25;
            float hue = (float) ((coord - timeVal * 0.4) % 1.0);
            if (hue < 0) hue += 1.0f;
            Color hsb = Color.getHSBColor(hue, 0.9f, (float) masterBrightness);
            return hsb;
        }

        if (simulationMode == SimulationMode.RADIAL_PULSE) {
            // Expanding concentric rings from DJ booth (0, 5.5)
            double dist = Math.sqrt(p.getX() * p.getX() + Math.pow(p.getY() - 5.5, 2));
            double wave = Math.sin(dist * 1.5 - timeVal * 5.0);
            wave = Math.max(0.0, wave);
            int r = (int) (255 * wave * masterBrightness);
            int g = (int) (180 * wave * masterBrightness);
            int b = (int) (50 * wave * masterBrightness);
            return new Color(r, g, b);
        }

        if (simulationMode == SimulationMode.RAINBOW_CLOUD) {
            float hue = (float) (((p.getX() * 0.08) + (p.getY() * 0.08) + (p.getZ() * 0.12) + timeVal * 0.2) % 1.0);
            if (hue < 0) hue += 1.0f;
            return Color.getHSBColor(hue, 0.85f, (float) masterBrightness);
        }

        if (simulationMode == SimulationMode.LINEAR_GRADIENT) {
            // Stage North (cyan) to FOH South (magenta)
            double normY = Math.max(0.0, Math.min(1.0, (p.getY() + 6.0) / 12.0));
            int r = (int) (( normY * 255 + (1 - normY) * 0 ) * masterBrightness);
            int g = (int) (( normY * 50 + (1 - normY) * 200 ) * masterBrightness);
            int b = (int) (( normY * 220 + (1 - normY) * 255 ) * masterBrightness);
            return new Color(Math.min(255, r), Math.min(255, g), Math.min(255, b));
        }

        // --- TIMELINE MODE: Evaluate active sequence cues ---
        if (player != null) {
            Set<String> activeIds = player.getActiveCueIds();
            if (activeIds.isEmpty() || !player.isPlaying()) {
                // All lights strictly off when stopped or idle
                return Color.BLACK;
            }

            Color accumulated = Color.BLACK;
            for (SequenceStep step : player.getActiveSteps()) {
                if (!matchesTarget(f, step)) continue;

                Color cueCol = calculateCueColor(step, pixelIndex, f.getPoints().size(), p, timeVal);
                accumulated = blendColors(accumulated, cueCol, step.getBlendMode());
            }
            return accumulated;
        }

        return Color.BLACK;
    }

    private boolean matchesTarget(FixtureModel f, SequenceStep step) {
        String grp = step.getFixtureGroup();
        if (grp != null && !grp.isBlank() && !grp.equalsIgnoreCase("all")) {
            if (!grp.equalsIgnoreCase(f.getGroup())) {
                return false;
            }
        }
        return true;
    }

    private Color calculateCueColor(SequenceStep step, int pixelIndex, int totalPixels, Point3D p, double timeVal) {
        String pat = step.getPatternId() != null ? step.getPatternId().toLowerCase() : "solid";
        double speed = step.getSpeed();
        double bright = step.getBrightness() * step.getTargetOpacity() * masterBrightness;
        Color prim = parseHex(step.getPrimaryColor());

        return switch (pat) {
            case "rainbow" -> {
                double offset = totalPixels > 1 ? (double) pixelIndex / totalPixels : 0.0;
                float hue = (float) ((offset + timeVal * speed * 0.2) % 1.0);
                if (hue < 0) hue += 1.0f;
                yield scaleBrightness(Color.getHSBColor(hue, 0.9f, 1.0f), bright);
            }
            case "chase" -> {
                double pos = (timeVal * speed * 25.0) % Math.max(1, totalPixels);
                double dist = Math.abs(pixelIndex - pos);
                double intensity = Math.max(0.0, 1.0 - (dist / 12.0));
                yield scaleBrightness(prim, bright * intensity);
            }
            case "fire" -> {
                double flicker = Math.sin(pixelIndex * 0.4 + timeVal * speed * 8.0) * 0.5 + 0.5;
                int r = (int) (255 * bright);
                int g = (int) (140 * flicker * bright);
                int b = (int) (20 * flicker * bright);
                yield new Color(r, Math.max(0, g), Math.max(0, b));
            }
            case "wave" -> {
                double w = Math.sin(pixelIndex * 0.08 + timeVal * speed * 4.0) * 0.5 + 0.5;
                yield scaleBrightness(prim, bright * w);
            }
            case "cylon" -> {
                double bounce = Math.abs(Math.sin(timeVal * speed * 2.0)) * totalPixels;
                double dist = Math.abs(pixelIndex - bounce);
                double intensity = Math.max(0.0, 1.0 - (dist / 8.0));
                yield scaleBrightness(prim, bright * intensity);
            }
            default -> scaleBrightness(prim, bright);
        };
    }

    private Color blendColors(Color base, Color overlay, String mode) {
        if ("OVERWRITE".equalsIgnoreCase(mode)) return overlay;
        if ("ADDITIVE".equalsIgnoreCase(mode)) {
            int r = Math.min(255, base.getRed() + overlay.getRed());
            int g = Math.min(255, base.getGreen() + overlay.getGreen());
            int b = Math.min(255, base.getBlue() + overlay.getBlue());
            return new Color(r, g, b);
        }
        // Alpha blend (50/50 mix)
        int r = (base.getRed() + overlay.getRed()) / 2;
        int g = (base.getGreen() + overlay.getGreen()) / 2;
        int b = (base.getBlue() + overlay.getBlue()) / 2;
        return new Color(r, g, b);
    }

    private Color getStandbyGlow(FixtureModel f) {
        return switch (f.getGroup().toLowerCase()) {
            case "festoon" -> new Color(90, 50, 15);
            case "panels" -> new Color(15, 35, 60);
            case "lamps" -> new Color(40, 25, 60);
            case "projectors" -> new Color(30, 45, 70);
            default -> new Color(25, 45, 65);
        };
    }

    private Color scaleBrightness(Color c, double factor) {
        float b = (float) Math.max(0.0, Math.min(1.0, factor));
        int r = (int) (c.getRed() * b);
        int g = (int) (c.getGreen() * b);
        int bl = (int) (c.getBlue() * b);
        return new Color(r, g, bl);
    }

    private Color parseHex(String hex) {
        if (hex == null || !hex.startsWith("#") || hex.length() < 7) {
            return Color.RED;
        }
        try {
            return Color.decode(hex);
        } catch (Exception e) {
            return Color.RED;
        }
    }

    // --- High-DPI Paint Component ---

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2 = (Graphics2D) g.create();

        // Enable professional desktop antialiasing
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g2.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
        g2.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
        g2.setRenderingHint(RenderingHints.KEY_STROKE_CONTROL, RenderingHints.VALUE_STROKE_PURE);

        // 1. Draw Architectural Blueprint Floorplan & Grid
        if (showGrid) {
            drawBlueprintGrid(g2);
        }
        if (showBlueprint) {
            drawStageArchitecture(g2);
        }

        // 2. Draw Floor Lamp Ambient Diffusion Pools
        drawLampFloorPools(g2);

        // 3. Draw Projector Screen & Throw Beams
        if (showBeams) {
            drawProjectorBeams(g2);
        }

        // 4. Draw Fixtures
        if (universe != null) {
            for (FixtureModel f : universe.getFixtures()) {
                drawFixture(g2, f);
            }
        }

        // 5. Draw Selection Reticles & Hover Highlights
        drawSelectionAndHover(g2);

        // 6. Draw HUD Overlays & Tooltips
        drawHudOverlay(g2);
        if (hoveredFixture != null && lastHoverPoint != null) {
            drawHoverTooltip(g2, hoveredFixture, lastHoverPoint);
        }

        g2.dispose();
    }

    private void drawBlueprintGrid(Graphics2D g2) {
        double minX = -8.0, maxX = 8.0;
        double minY = -8.0, maxY = 8.0;

        g2.setFont(FONT_ARIAL_PLAIN_10);

        // 1-meter grid
        for (double x = minX; x <= maxX; x += 1.0) {
            double sx = worldToScreenX(x);
            if (Math.abs(x) < 0.001) {
                g2.setColor(new Color(45, 75, 115, 120)); // Center axis
                g2.setStroke(new BasicStroke(1.5f));
            } else {
                g2.setColor(new Color(28, 42, 65, 80));
                g2.setStroke(new BasicStroke(1.0f));
            }
            g2.draw(new Line2D.Double(sx, 0, sx, getHeight()));

            if (showLabels && Math.abs(x % 2.0) < 0.001) {
                g2.setColor(new Color(90, 130, 180, 140));
                g2.drawString(String.format("%+.0fm", x), (float) sx + 4, getHeight() - 12);
            }
        }

        for (double y = minY; y <= maxY; y += 1.0) {
            double sy = worldToScreenY(y);
            if (Math.abs(y) < 0.001) {
                g2.setColor(new Color(45, 75, 115, 120)); // Center axis
                g2.setStroke(new BasicStroke(1.5f));
            } else {
                g2.setColor(new Color(28, 42, 65, 80));
                g2.setStroke(new BasicStroke(1.0f));
            }
            g2.draw(new Line2D.Double(0, sy, getWidth(), sy));

            if (showLabels && Math.abs(y % 2.0) < 0.001) {
                g2.setColor(new Color(90, 130, 180, 140));
                g2.drawString(String.format("%+.0fm", y), 8, (float) sy - 4);
            }
        }
    }

    private void drawStageArchitecture(Graphics2D g2) {
        // Venue Boundary Box (13.0m x 13.5m)
        double sx0 = worldToScreenX(-6.5);
        double sy0 = worldToScreenY(7.0);
        double sw = 13.0 * zoom;
        double sh = 13.5 * zoom;

        g2.setColor(new Color(35, 55, 85, 100));
        g2.setStroke(new BasicStroke(2.0f));
        g2.draw(new Rectangle2D.Double(sx0, sy0, sw, sh));

        // Main Stage Proscenium Deck [-5.0, 3.5] to [5.0, 7.0]
        double stageX = worldToScreenX(-5.0);
        double stageY = worldToScreenY(7.0);
        double stageW = 10.0 * zoom;
        double stageH = 3.5 * zoom;

        g2.setColor(new Color(22, 34, 52, 140));
        g2.fill(new Rectangle2D.Double(stageX, stageY, stageW, stageH));
        g2.setColor(new Color(55, 90, 135, 160));
        g2.setStroke(new BasicStroke(1.5f));
        g2.draw(new Rectangle2D.Double(stageX, stageY, stageW, stageH));

        // Stage Proscenium Lip Glow
        double lipY = worldToScreenY(3.5);
        g2.setColor(new Color(70, 130, 200, 200));
        g2.setStroke(new BasicStroke(2.5f));
        g2.draw(new Line2D.Double(stageX, lipY, stageX + stageW, lipY));

        // DJ Riser / Performance console [-1.8, 4.8] to [1.8, 6.2]
        double djX = worldToScreenX(-1.8);
        double djY = worldToScreenY(6.2);
        double djW = 3.6 * zoom;
        double djH = 1.4 * zoom;

        g2.setColor(new Color(28, 45, 70, 200));
        g2.fill(new RoundRectangle2D.Double(djX, djY, djW, djH, 6, 6));
        g2.setColor(new Color(80, 140, 210, 220));
        g2.setStroke(new BasicStroke(1.5f));
        g2.draw(new RoundRectangle2D.Double(djX, djY, djW, djH, 6, 6));

        // FOH Console [-1.5, -4.5] to [1.5, -3.5]
        double fohX = worldToScreenX(-1.5);
        double fohY = worldToScreenY(-3.5);
        double fohW = 3.0 * zoom;
        double fohH = 1.0 * zoom;

        g2.setColor(new Color(24, 38, 58, 180));
        g2.fill(new RoundRectangle2D.Double(fohX, fohY, fohW, fohH, 6, 6));
        g2.setColor(new Color(65, 110, 165, 180));
        g2.setStroke(new BasicStroke(1.2f));
        g2.draw(new RoundRectangle2D.Double(fohX, fohY, fohW, fohH, 6, 6));

        // Venue Blueprint Text Labels
        if (showLabels) {
            g2.setFont(FONT_ARIAL_BOLD_11);
            g2.setColor(new Color(110, 160, 220, 180));
            g2.drawString("STAGE PROSCENIUM", (float) (stageX + 12), (float) (stageY + 20));
            g2.drawString("DJ PERFORMANCE RISER", (float) (djX + 8), (float) (djY + 18));
            g2.drawString("FOH SOUND & LIGHTING CONSOLE", (float) (fohX + 10), (float) (fohY + 16));

            g2.setFont(FONT_ARIAL_PLAIN_10);
            g2.setColor(new Color(75, 115, 165, 130));
            g2.drawString("UPSTAGE (NORTH)", (float) (worldToScreenX(0.0) - 55), (float) worldToScreenY(6.8));
            g2.drawString("AUDIENCE / FOH (SOUTH)", (float) (worldToScreenX(0.0) - 75), (float) worldToScreenY(-6.2));
        }
    }

    private void drawLampFloorPools(Graphics2D g2) {
        if (universe == null) return;

        for (FixtureModel f : universe.getFixtures()) {
            if (!"point".equalsIgnoreCase(f.getType())) continue;

            Point3D loc = f.getPoints().isEmpty() ? new Point3D(0, 0, 0) : f.getPoints().get(0);
            double sx = worldToScreenX(loc.getX());
            double sy = worldToScreenY(loc.getY());

            double rWorld = Math.max(0.6, f.getRadius() * 2.2);
            float rPixels = (float) (rWorld * zoom);

            List<Color> colors = fixtureColorCache.get(f.getId());
            Color lampCol = (colors != null && !colors.isEmpty()) ? colors.get(0) : new Color(255, 180, 50);

            Color coreGlow = new Color(lampCol.getRed(), lampCol.getGreen(), lampCol.getBlue(), 120);
            Color edgeGlow = new Color(lampCol.getRed(), lampCol.getGreen(), lampCol.getBlue(), 0);

            try {
                RadialGradientPaint rgp = new RadialGradientPaint(
                        new Point2D.Float((float) sx, (float) sy),
                        Math.max(4.0f, rPixels),
                        new float[]{0.0f, 1.0f},
                        new Color[]{coreGlow, edgeGlow}
                );
                g2.setPaint(rgp);
                g2.fill(new Ellipse2D.Double(sx - rPixels, sy - rPixels, rPixels * 2, rPixels * 2));
            } catch (Exception ignored) {}
        }
    }

    private void drawProjectorBeams(Graphics2D g2) {
        if (universe == null) return;
        FixtureModel proj = universe.getFixture("projector_stage_canvas");
        if (proj == null) return;

        Point3D tl = proj.getTopLeft() != null ? proj.getTopLeft() : new Point3D(-2.4, 6.9, 3.8);
        Point3D br = proj.getBottomRight() != null ? proj.getBottomRight() : new Point3D(2.4, 6.9, 1.1);

        double screenLeftX = worldToScreenX(tl.getX());
        double screenRightX = worldToScreenX(br.getX());
        double screenY = worldToScreenY(tl.getY());

        // Virtual projector throw origin in venue center (0, 0)
        double throwOriginX = worldToScreenX(0.0);
        double throwOriginY = worldToScreenY(0.0);

        // Beam polygon
        Path2D beamPath = new Path2D.Double();
        beamPath.moveTo(throwOriginX, throwOriginY);
        beamPath.lineTo(screenLeftX, screenY);
        beamPath.lineTo(screenRightX, screenY);
        beamPath.closePath();

        Color beamColor = new Color(40, 120, 220, 25);
        g2.setColor(beamColor);
        g2.fill(beamPath);

        g2.setColor(new Color(60, 160, 255, 70));
        g2.setStroke(new BasicStroke(1.0f, BasicStroke.CAP_BUTT, BasicStroke.JOIN_BEVEL, 0, new float[]{6, 6}, 0));
        g2.draw(new Line2D.Double(throwOriginX, throwOriginY, screenLeftX, screenY));
        g2.draw(new Line2D.Double(throwOriginX, throwOriginY, screenRightX, screenY));
    }

    private void drawFixture(Graphics2D g2, FixtureModel f) {
        String type = f.getType().toLowerCase();
        List<Color> colors = fixtureColorCache.get(f.getId());

        switch (type) {
            case "linear_strip" -> drawLinearStrip(g2, f, colors);
            case "bulb_string" -> drawBulbString(g2, f, colors);
            case "matrix" -> drawMatrix(g2, f, colors);
            case "point" -> drawPointLamp(g2, f, colors);
            case "projector" -> drawProjectorScreen(g2, f);
            default -> drawGenericFixture(g2, f, colors);
        }
    }

    private void drawLinearStrip(Graphics2D g2, FixtureModel f, List<Color> colors) {
        List<Point3D> points = f.getPoints();
        if (points.isEmpty()) return;

        // Structural truss backing line
        if (points.size() > 1) {
            Point3D p0 = points.get(0);
            Point3D pN = points.get(points.size() - 1);
            g2.setColor(new Color(40, 55, 75, 160));
            g2.setStroke(new BasicStroke(4.0f, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND));
            g2.draw(new Line2D.Double(worldToScreenX(p0.getX()), worldToScreenY(p0.getY()),
                    worldToScreenX(pN.getX()), worldToScreenY(pN.getY())));
        }

        // Draw individual LED diodes
        double diodeRadius = Math.max(1.8, Math.min(3.5, zoom * 0.05));
        int count = points.size();

        for (int i = 0; i < count; i++) {
            Point3D p = points.get(i);
            double sx = worldToScreenX(p.getX());
            double sy = worldToScreenY(p.getY());

            Color c = (colors != null && i < colors.size()) ? colors.get(i) : Color.DARK_GRAY;

            // Diode core
            g2.setColor(c);
            g2.fill(new Ellipse2D.Double(sx - diodeRadius, sy - diodeRadius, diodeRadius * 2, diodeRadius * 2));

            // Subtle glow if bright
            if (c.getRed() + c.getGreen() + c.getBlue() > 100) {
                g2.setColor(new Color(c.getRed(), c.getGreen(), c.getBlue(), 60));
                g2.fill(new Ellipse2D.Double(sx - diodeRadius * 2, sy - diodeRadius * 2, diodeRadius * 4, diodeRadius * 4));
            }
        }
    }

    private void drawBulbString(Graphics2D g2, FixtureModel f, List<Color> colors) {
        List<Point3D> points = f.getPoints();
        if (points.isEmpty()) return;

        // Draw catenary suspension cable
        Path2D path = new Path2D.Double();
        Point3D first = points.get(0);
        path.moveTo(worldToScreenX(first.getX()), worldToScreenY(first.getY()));

        for (int i = 1; i < points.size(); i++) {
            Point3D p = points.get(i);
            path.lineTo(worldToScreenX(p.getX()), worldToScreenY(p.getY()));
        }

        g2.setColor(new Color(60, 50, 40, 180));
        g2.setStroke(new BasicStroke(1.8f));
        g2.draw(path);

        // Draw warm Edison-style bulb globes
        double bulbRadius = Math.max(3.5, Math.min(7.0, zoom * 0.12));

        for (int i = 0; i < points.size(); i++) {
            Point3D p = points.get(i);
            double sx = worldToScreenX(p.getX());
            double sy = worldToScreenY(p.getY());

            Color c = (colors != null && i < colors.size()) ? colors.get(i) : Color.BLACK;
            boolean isLit = (c.getRed() + c.getGreen() + c.getBlue() > 15);

            // Translucent glass globe
            if (isLit) {
                g2.setColor(new Color(c.getRed(), c.getGreen(), c.getBlue(), 80));
                g2.fill(new Ellipse2D.Double(sx - bulbRadius, sy - bulbRadius, bulbRadius * 2, bulbRadius * 2));
            } else {
                g2.setColor(new Color(25, 25, 30, 100));
                g2.fill(new Ellipse2D.Double(sx - bulbRadius, sy - bulbRadius, bulbRadius * 2, bulbRadius * 2));
            }

            // Glass outline
            g2.setColor(isLit ? new Color(255, 230, 180, 200) : new Color(55, 60, 70, 140));
            g2.setStroke(new BasicStroke(1.0f));
            g2.draw(new Ellipse2D.Double(sx - bulbRadius, sy - bulbRadius, bulbRadius * 2, bulbRadius * 2));

            // Hot inner filament core
            g2.setColor(isLit ? c : new Color(35, 35, 40));
            double filRad = bulbRadius * 0.45;
            g2.fill(new Ellipse2D.Double(sx - filRad, sy - filRad, filRad * 2, filRad * 2));
        }
    }

    private void drawMatrix(Graphics2D g2, FixtureModel f, List<Color> colors) {
        Point3D org = f.getOrigin() != null ? f.getOrigin() : new Point3D(0, 0, 0);
        double sx = worldToScreenX(org.getX());
        double sy = worldToScreenY(org.getZ() > 0 ? org.getY() : org.getY()); // orthographic
        double sw = f.getWidth() * zoom;
        double sh = Math.max(12.0, f.getHeight() * zoom * 0.4); // perspective tilt

        // Outer chassis
        g2.setColor(new Color(20, 28, 40, 220));
        g2.fill(new RoundRectangle2D.Double(sx, sy, sw, sh, 4, 4));
        g2.setColor(new Color(50, 85, 130, 220));
        g2.setStroke(new BasicStroke(1.2f));
        g2.draw(new RoundRectangle2D.Double(sx, sy, sw, sh, 4, 4));

        // High density LED matrix dots
        List<Point3D> points = f.getPoints();
        int rCount = f.getRows() > 0 ? f.getRows() : 16;
        int cCount = f.getCols() > 0 ? f.getCols() : 16;

        double dotPitchX = sw / Math.max(1, cCount);
        double dotPitchY = sh / Math.max(1, rCount);
        double dotRad = Math.max(1.2, Math.min(2.5, dotPitchX * 0.35));

        for (int r = 0; r < rCount; r++) {
            for (int c = 0; c < cCount; c++) {
                int idx = r * cCount + c;
                Color col = (colors != null && idx < colors.size()) ? colors.get(idx) : Color.BLACK;

                double px = sx + c * dotPitchX + dotPitchX / 2.0;
                double py = sy + r * dotPitchY + dotPitchY / 2.0;

                g2.setColor(col);
                g2.fill(new Ellipse2D.Double(px - dotRad, py - dotRad, dotRad * 2, dotRad * 2));
            }
        }
    }

    private void drawPointLamp(Graphics2D g2, FixtureModel f, List<Color> colors) {
        Point3D loc = f.getPoints().isEmpty() ? new Point3D(0, 0, 0) : f.getPoints().get(0);
        double sx = worldToScreenX(loc.getX());
        double sy = worldToScreenY(loc.getY());

        Color c = (colors != null && !colors.isEmpty()) ? colors.get(0) : Color.BLACK;
        boolean isLit = (c.getRed() + c.getGreen() + c.getBlue() > 15);

        // Chrome stand base
        double baseRadius = Math.max(4.0, zoom * 0.1);
        g2.setColor(new Color(30, 42, 60));
        g2.fill(new Ellipse2D.Double(sx - baseRadius, sy - baseRadius, baseRadius * 2, baseRadius * 2));
        g2.setColor(new Color(120, 160, 210));
        g2.setStroke(new BasicStroke(1.5f));
        g2.draw(new Ellipse2D.Double(sx - baseRadius, sy - baseRadius, baseRadius * 2, baseRadius * 2));

        // Lamp emitter
        g2.setColor(isLit ? c : new Color(20, 20, 25));
        double emitterRad = baseRadius * 0.6;
        g2.fill(new Ellipse2D.Double(sx - emitterRad, sy - emitterRad, emitterRad * 2, emitterRad * 2));
        if (isLit) {
            g2.setColor(new Color(c.getRed(), c.getGreen(), c.getBlue(), 60));
            g2.fill(new Ellipse2D.Double(sx - emitterRad * 2, sy - emitterRad * 2, emitterRad * 4, emitterRad * 4));
        }
    }

    private void drawProjectorScreen(Graphics2D g2, FixtureModel f) {
        Point3D tl = f.getTopLeft() != null ? f.getTopLeft() : new Point3D(-2.4, 6.9, 3.8);
        Point3D br = f.getBottomRight() != null ? f.getBottomRight() : new Point3D(2.4, 6.9, 1.1);

        double sx = worldToScreenX(tl.getX());
        double sy = worldToScreenY(tl.getY());
        double sw = (br.getX() - tl.getX()) * zoom;
        double sh = Math.max(8.0, 12.0); // Projection screen thickness in top-down view

        // Screen frame
        g2.setColor(new Color(15, 20, 30));
        g2.fill(new Rectangle2D.Double(sx, sy - sh / 2.0, sw, sh));
        g2.setColor(new Color(80, 130, 200));
        g2.setStroke(new BasicStroke(2.0f));
        g2.draw(new Rectangle2D.Double(sx, sy - sh / 2.0, sw, sh));

        // Projected image glow on screen surface
        g2.setColor(new Color(180, 220, 255, 200));
        g2.setStroke(new BasicStroke(2.5f));
        g2.draw(new Line2D.Double(sx, sy + sh / 2.0, sx + sw, sy + sh / 2.0));
    }

    private void drawGenericFixture(Graphics2D g2, FixtureModel f, List<Color> colors) {
        for (int i = 0; i < f.getPoints().size(); i++) {
            Point3D p = f.getPoints().get(i);
            double sx = worldToScreenX(p.getX());
            double sy = worldToScreenY(p.getY());
            Color c = (colors != null && i < colors.size()) ? colors.get(i) : Color.WHITE;
            g2.setColor(c);
            g2.fill(new Ellipse2D.Double(sx - 2, sy - 2, 4, 4));
        }
    }

    private void drawSelectionAndHover(Graphics2D g2) {
        if (hoveredFixture != null && hoveredFixture != selectedFixture) {
            drawFixtureHalo(g2, hoveredFixture, new Color(100, 200, 255, 140), 1.5f);
        }
        if (selectedFixture != null) {
            drawFixtureHalo(g2, selectedFixture, new Color(255, 200, 40, 230), 2.5f);
        }
    }

    private void drawFixtureHalo(Graphics2D g2, FixtureModel f, Color haloColor, float strokeWidth) {
        List<Point3D> points = f.getPoints();
        if (points.isEmpty()) return;

        double minSx = Double.MAX_VALUE, minSy = Double.MAX_VALUE;
        double maxSx = -Double.MAX_VALUE, maxSy = -Double.MAX_VALUE;

        for (Point3D p : points) {
            double sx = worldToScreenX(p.getX());
            double sy = worldToScreenY(p.getY());
            if (sx < minSx) minSx = sx;
            if (sx > maxSx) maxSx = sx;
            if (sy < minSy) minSy = sy;
            if (sy > maxSy) maxSy = sy;
        }

        double pad = 8.0;
        double w = Math.max(16.0, maxSx - minSx + pad * 2);
        double h = Math.max(16.0, maxSy - minSy + pad * 2);

        g2.setColor(haloColor);
        g2.setStroke(new BasicStroke(strokeWidth, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND, 0, new float[]{6, 4}, (float) (simTimeSec * 10)));
        g2.draw(new RoundRectangle2D.Double(minSx - pad, minSy - pad, w, h, 8, 8));
    }

    private void drawHudOverlay(Graphics2D g2) {
        // Top-left venue telemetry pill
        int pad = 12;
        int hudW = 340;
        int hudH = 56;

        g2.setColor(new Color(18, 25, 38, 220));
        g2.fill(new RoundRectangle2D.Double(pad, pad, hudW, hudH, 8, 8));
        g2.setColor(new Color(45, 65, 95));
        g2.setStroke(new BasicStroke(1.0f));
        g2.draw(new RoundRectangle2D.Double(pad, pad, hudW, hudH, 8, 8));

        g2.setFont(FONT_ARIAL_BOLD_12);
        g2.setColor(new Color(240, 245, 255));
        String title = universe != null ? universe.getName() : "Metro Concert Hall & Lounge";
        g2.drawString(title, pad + 10, pad + 20);

        g2.setFont(FONT_ARIAL_PLAIN_11);
        g2.setColor(new Color(140, 180, 220));
        int totalFix = universe != null ? universe.getFixtures().size() : 28;
        int totalPix = universe != null ? universe.getTotalPixels() : 5153;
        int totalCtrl = patchTable != null ? patchTable.getAllControllers().size() : 20;

        g2.drawString(String.format("%d Fixtures | %,d LEDs | %d Nodes", totalFix, totalPix, totalCtrl), pad + 10, pad + 36);

        // Cat6 broadcast sync indicator
        g2.setColor(new Color(40, 200, 90));
        g2.drawString("Cat6 DDP Sync Active (0x41)", pad + 10, pad + 50);

        // Bottom-left navigation hint
        g2.setFont(FONT_ARIAL_PLAIN_11);
        g2.setColor(new Color(120, 150, 190, 180));
        String hint = String.format("Scale: %.1f px/m | Pan: Drag | Zoom: Wheel | [F] Fit View", zoom);
        g2.drawString(hint, 12, getHeight() - 10);
    }

    private void drawHoverTooltip(Graphics2D g2, FixtureModel f, Point mousePos) {
        int tx = mousePos.x + 15;
        int ty = mousePos.y + 15;
        if (tx + 260 > getWidth()) tx = mousePos.x - 270;
        if (ty + 90 > getHeight()) ty = mousePos.y - 95;

        int tw = 255;
        int th = 80;

        g2.setColor(new Color(24, 32, 48, 240));
        g2.fill(new RoundRectangle2D.Double(tx, ty, tw, th, 8, 8));
        g2.setColor(new Color(70, 120, 190, 220));
        g2.setStroke(new BasicStroke(1.2f));
        g2.draw(new RoundRectangle2D.Double(tx, ty, tw, th, 8, 8));

        g2.setFont(FONT_ARIAL_BOLD_12);
        g2.setColor(Color.WHITE);
        g2.drawString(f.getName(), tx + 10, ty + 20);

        g2.setFont(FONT_ARIAL_PLAIN_11);
        g2.setColor(new Color(150, 190, 240));
        g2.drawString("Group: " + f.getGroup().toUpperCase() + " | Type: " + f.getType(), tx + 10, ty + 38);
        g2.drawString(String.format("LEDs: %,d pixels | Order: %s", f.getPixelCount(), f.getColorOrder()), tx + 10, ty + 54);

        // Hardware patch lookup
        String patchInfo = "Patched: wled_01 (CH0)";
        if (patchTable != null) {
            List<PatchSegmentModel> segs = patchTable.getSegmentsForFixture(f.getId());
            if (!segs.isEmpty()) {
                PatchSegmentModel s0 = segs.get(0);
                patchInfo = String.format("Node: %s (CH%d, %s)", s0.getControllerId(), s0.getChannelIndex(), s0.getProtocol().toUpperCase());
            }
        }
        g2.setColor(new Color(90, 215, 130));
        g2.drawString(patchInfo, tx + 10, ty + 70);
    }
}
