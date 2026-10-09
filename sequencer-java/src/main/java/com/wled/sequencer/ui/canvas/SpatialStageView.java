package com.wled.sequencer.ui.canvas;

import com.wled.sequencer.player.TimelinePlayer;
import com.wled.sequencer.universe.FixtureModel;
import com.wled.sequencer.universe.PatchSegmentModel;
import com.wled.sequencer.universe.PatchTableModel;
import com.wled.sequencer.universe.Point3D;
import com.wled.sequencer.universe.SpatialUniverseModel;

import javax.swing.*;
import javax.swing.border.EmptyBorder;
import javax.swing.tree.DefaultMutableTreeNode;
import javax.swing.tree.DefaultTreeModel;
import javax.swing.tree.TreePath;
import javax.swing.tree.TreeSelectionModel;
import java.awt.*;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

/**
 * Composite Spatial Stage Universe view incorporating 2D canvas,
 * camera controls toolbar, lighting simulation modes, and fixture hierarchy browser with full editing.
 * Uses default Swing settings and Arial font throughout.
 */
public class SpatialStageView extends JPanel {
    private final StageCanvasPanel canvasPanel;
    private SpatialUniverseModel universe;
    private PatchTableModel patchTable;

    // Stage Preset Selector
    private final JComboBox<String> cmbStagePreset = new JComboBox<>(new String[]{
            "Metro Concert Hall & Lounge",
            "Warehouse Rave & Boiler Stage",
            "Outdoor Amphitheater & Lawn",
            "Immersive Art Gallery & Studio"
    });
    private java.util.function.Consumer<String> onStagePresetSelectedListener;
    private boolean suppressPresetEvent = false;

    // Simulation selector promoted to field for programmatic synchronization
    private final JComboBox<String> cmbSimMode = new JComboBox<>(new String[]{
            "Timeline Cues (Player)",
            "45 Deg Angle Sweep",
            "Radial Pulse",
            "Rainbow Cloud",
            "Linear Gradient",
            "Blackout All"
    });

    // Fixture Tree & Inspector
    private final JTree fixtureTree;
    private final DefaultMutableTreeNode rootNode;
    private final DefaultTreeModel treeModel;

    // Fixture Details Card
    private final JLabel lblDetailName = new JLabel("Select a Fixture");
    private final JLabel lblDetailType = new JLabel("-");
    private final JLabel lblDetailGroup = new JLabel("-");
    private final JLabel lblDetailPixels = new JLabel("-");
    private final JLabel lblDetailController = new JLabel("-");
    private final JLabel lblDetailCoords = new JLabel("-");

    public SpatialStageView(SpatialUniverseModel universe, PatchTableModel patchTable, TimelinePlayer player) {
        this.universe = universe;
        this.patchTable = patchTable;
        this.canvasPanel = new StageCanvasPanel(universe, patchTable, player);

        setLayout(new BorderLayout(4, 4));

        // 1. Top Camera & Simulation Controls Toolbar
        add(createCanvasToolBar(), BorderLayout.NORTH);

        // 2. Right Side: Fixture Tree & Details Inspector
        rootNode = new DefaultMutableTreeNode("Venue Universe (" + (universe != null ? universe.getTotalPixels() : 0) + " LEDs)");
        treeModel = new DefaultTreeModel(rootNode);
        fixtureTree = new JTree(treeModel);
        fixtureTree.getSelectionModel().setSelectionMode(TreeSelectionModel.SINGLE_TREE_SELECTION);

        populateFixtureTree();

        JSplitPane splitPane = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT, canvasPanel, createFixtureSidebar());
        splitPane.setResizeWeight(0.78);
        splitPane.setDividerSize(6);

        add(splitPane, BorderLayout.CENTER);

        // 3. Two-way synchronization between canvas selection and tree selection
        canvasPanel.setOnFixtureSelectedListener(this::selectFixtureInTree);

        fixtureTree.addTreeSelectionListener(e -> {
            TreePath path = e.getPath();
            if (path == null) return;
            DefaultMutableTreeNode node = (DefaultMutableTreeNode) path.getLastPathComponent();
            if (node.getUserObject() instanceof FixtureNodeItem item) {
                canvasPanel.setSelectedFixture(item.fixture());
                updateDetailsCard(item.fixture());
            } else {
                canvasPanel.setSelectedFixture(null);
                updateDetailsCard(null);
            }
        });
    }

    public StageCanvasPanel getCanvasPanel() {
        return canvasPanel;
    }

    public void setUniverse(SpatialUniverseModel universe) {
        this.universe = universe;
        this.canvasPanel.setUniverse(universe);
        populateFixtureTree();
    }

    public void setPatchTable(PatchTableModel patchTable) {
        this.patchTable = patchTable;
        this.canvasPanel.setPatchTable(patchTable);
        populateFixtureTree();
    }

    public void blackout() {
        canvasPanel.blackout();
        cmbSimMode.setSelectedIndex(5);
    }

    public void setOnStagePresetSelectedListener(java.util.function.Consumer<String> listener) {
        this.onStagePresetSelectedListener = listener;
    }

    public void setStagePresetSelection(String name) {
        if (name == null) return;
        suppressPresetEvent = true;
        try {
            String lower = name.toLowerCase();
            if (lower.contains("warehouse") || lower.contains("rave") || lower.contains("boiler")) {
                cmbStagePreset.setSelectedIndex(1);
            } else if (lower.contains("amphitheater") || lower.contains("festival") || lower.contains("outdoor")) {
                cmbStagePreset.setSelectedIndex(2);
            } else if (lower.contains("gallery") || lower.contains("art") || lower.contains("studio")) {
                cmbStagePreset.setSelectedIndex(3);
            } else {
                cmbStagePreset.setSelectedIndex(0);
            }
        } finally {
            suppressPresetEvent = false;
        }
    }

    public void resetTimeline() {
        canvasPanel.resetTimeline();
        cmbSimMode.setSelectedIndex(0);
    }

    private JToolBar createCanvasToolBar() {
        JToolBar tb = new JToolBar();
        tb.setFloatable(false);
        tb.setBorder(BorderFactory.createEtchedBorder());

        // Stage Preset selector
        JLabel lblStage = new JLabel("Stage Preset: ");
        lblStage.setFont(new Font("Arial", Font.BOLD, 12));
        tb.add(lblStage);

        cmbStagePreset.setFont(new Font("Arial", Font.PLAIN, 12));
        cmbStagePreset.addActionListener(e -> {
            if (suppressPresetEvent || onStagePresetSelectedListener == null) return;
            String presetId = switch (cmbStagePreset.getSelectedIndex()) {
                case 1 -> "warehouse_rave";
                case 2 -> "festival_amphitheater";
                case 3 -> "art_gallery";
                default -> "concert_hall";
            };
            onStagePresetSelectedListener.accept(presetId);
        });
        tb.add(cmbStagePreset);

        tb.addSeparator(new Dimension(14, 24));

        // Camera presets
        JButton btnFit = new JButton("Fit Stage");
        JButton btnReset = new JButton("1:1 Reset");
        JButton btnZoomIn = new JButton("+ Zoom");
        JButton btnZoomOut = new JButton("- Zoom");

        btnFit.addActionListener(e -> canvasPanel.fitView());
        btnReset.addActionListener(e -> canvasPanel.resetView());
        btnZoomIn.addActionListener(e -> canvasPanel.zoomIn());
        btnZoomOut.addActionListener(e -> canvasPanel.zoomOut());

        tb.add(btnFit);
        tb.add(btnReset);
        tb.add(btnZoomIn);
        tb.add(btnZoomOut);

        tb.addSeparator(new Dimension(14, 24));

        // Layer toggles
        JCheckBox chkGrid = new JCheckBox("Grid", true);
        JCheckBox chkBlueprint = new JCheckBox("Blueprint", true);
        JCheckBox chkLabels = new JCheckBox("Labels", true);
        JCheckBox chkBeams = new JCheckBox("Beams", true);

        chkGrid.addActionListener(e -> canvasPanel.toggleGrid());
        chkBlueprint.addActionListener(e -> canvasPanel.toggleBlueprint());
        chkLabels.addActionListener(e -> canvasPanel.toggleLabels());
        chkBeams.addActionListener(e -> canvasPanel.toggleBeams());

        tb.add(chkGrid);
        tb.add(chkBlueprint);
        tb.add(chkLabels);
        tb.add(chkBeams);

        tb.addSeparator(new Dimension(14, 24));

        // Simulation Mode Selector
        tb.add(new JLabel("Live FX: "));
        cmbSimMode.addActionListener(e -> {
            int idx = cmbSimMode.getSelectedIndex();
            StageCanvasPanel.SimulationMode mode = switch (idx) {
                case 1 -> StageCanvasPanel.SimulationMode.ANGLE_SWEEP;
                case 2 -> StageCanvasPanel.SimulationMode.RADIAL_PULSE;
                case 3 -> StageCanvasPanel.SimulationMode.RAINBOW_CLOUD;
                case 4 -> StageCanvasPanel.SimulationMode.LINEAR_GRADIENT;
                case 5 -> StageCanvasPanel.SimulationMode.BLACKOUT;
                default -> StageCanvasPanel.SimulationMode.TIMELINE;
            };
            canvasPanel.setSimulationMode(mode);
        });
        tb.add(cmbSimMode);

        tb.addSeparator(new Dimension(12, 24));

        // Master Brightness Slider
        tb.add(new JLabel("Brightness: "));
        JSlider sldBrightness = new JSlider(0, 100, 100);
        sldBrightness.setPreferredSize(new Dimension(90, 22));
        sldBrightness.addChangeListener(e -> canvasPanel.setMasterBrightness(sldBrightness.getValue() / 100.0));
        tb.add(sldBrightness);

        return tb;
    }

    private JPanel createFixtureSidebar() {
        JPanel sidebar = new JPanel(new BorderLayout(4, 4));
        sidebar.setBorder(BorderFactory.createTitledBorder("Fixture Universe & Hardware Patch"));
        sidebar.setPreferredSize(new Dimension(300, 500));

        // Fixture Tree in scroll pane
        fixtureTree.setFont(new Font("Arial", Font.PLAIN, 12));
        JScrollPane treeScroll = new JScrollPane(fixtureTree);
        treeScroll.setBorder(BorderFactory.createEtchedBorder());
        sidebar.add(treeScroll, BorderLayout.CENTER);

        // Lower panel containing Action Toolbar and Details Card
        JPanel lowerPanel = new JPanel(new BorderLayout(4, 4));

        // Fixture Action Toolbar (Add / Edit / Delete / Save)
        JPanel actionToolbar = new JPanel(new FlowLayout(FlowLayout.CENTER, 4, 2));
        JButton btnAddFix = new JButton("Add");
        JButton btnEditFix = new JButton("Edit");
        JButton btnDelFix = new JButton("Delete");
        JButton btnSaveUni = new JButton("Save Universe");
        btnSaveUni.setFont(new Font("Arial", Font.BOLD, 11));

        btnAddFix.addActionListener(e -> showAddEditFixtureDialog(null));
        btnEditFix.addActionListener(e -> {
            FixtureModel sel = getSelectedFixtureFromTree();
            if (sel != null) {
                showAddEditFixtureDialog(sel);
            } else {
                JOptionPane.showMessageDialog(this, "Please select a fixture in the tree to edit.", "Selection Required", JOptionPane.WARNING_MESSAGE);
            }
        });
        btnDelFix.addActionListener(e -> {
            FixtureModel sel = getSelectedFixtureFromTree();
            if (sel != null) {
                int confirm = JOptionPane.showConfirmDialog(this,
                        "Are you sure you want to delete fixture '" + sel.getName() + "' (" + sel.getId() + ")?",
                        "Confirm Deletion", JOptionPane.YES_NO_OPTION);
                if (confirm == JOptionPane.YES_OPTION) {
                    universe.removeFixture(sel.getId());
                    populateFixtureTree();
                    canvasPanel.setSelectedFixture(null);
                    canvasPanel.repaint();
                    updateDetailsCard(null);
                }
            } else {
                JOptionPane.showMessageDialog(this, "Please select a fixture in the tree to delete.", "Selection Required", JOptionPane.WARNING_MESSAGE);
            }
        });
        btnSaveUni.addActionListener(e -> saveUniverseToFile());

        actionToolbar.add(btnAddFix);
        actionToolbar.add(btnEditFix);
        actionToolbar.add(btnDelFix);
        actionToolbar.add(btnSaveUni);

        lowerPanel.add(actionToolbar, BorderLayout.NORTH);

        // Fixture details inspector card
        JPanel detailsCard = new JPanel(new GridBagLayout());
        detailsCard.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createTitledBorder("Selected Fixture Details"),
                new EmptyBorder(4, 6, 6, 6)
        ));

        GridBagConstraints g = new GridBagConstraints();
        g.insets = new Insets(2, 4, 2, 4);
        g.anchor = GridBagConstraints.WEST;
        g.fill = GridBagConstraints.HORIZONTAL;

        lblDetailName.setFont(new Font("Arial", Font.BOLD, 12));
        g.gridx = 0; g.gridy = 0; g.gridwidth = 2;
        detailsCard.add(lblDetailName, g);
        g.gridwidth = 1;

        g.gridx = 0; g.gridy = 1;
        detailsCard.add(new JLabel("Type:"), g);
        g.gridx = 1;
        detailsCard.add(lblDetailType, g);

        g.gridx = 0; g.gridy = 2;
        detailsCard.add(new JLabel("Group:"), g);
        g.gridx = 1;
        detailsCard.add(lblDetailGroup, g);

        g.gridx = 0; g.gridy = 3;
        detailsCard.add(new JLabel("LEDs:"), g);
        g.gridx = 1;
        detailsCard.add(lblDetailPixels, g);

        g.gridx = 0; g.gridy = 4;
        detailsCard.add(new JLabel("Controller:"), g);
        g.gridx = 1;
        detailsCard.add(lblDetailController, g);

        g.gridx = 0; g.gridy = 5;
        detailsCard.add(new JLabel("Location:"), g);
        g.gridx = 1;
        detailsCard.add(lblDetailCoords, g);

        lowerPanel.add(detailsCard, BorderLayout.SOUTH);

        sidebar.add(lowerPanel, BorderLayout.SOUTH);

        return sidebar;
    }

    private FixtureModel getSelectedFixtureFromTree() {
        TreePath path = fixtureTree.getSelectionPath();
        if (path == null) return null;
        DefaultMutableTreeNode node = (DefaultMutableTreeNode) path.getLastPathComponent();
        if (node.getUserObject() instanceof FixtureNodeItem item) {
            return item.fixture();
        }
        return null;
    }

    private void showAddEditFixtureDialog(FixtureModel existing) {
        boolean isEdit = (existing != null);

        JTextField txtId = new JTextField(isEdit ? existing.getId() : "fixture_" + (universe != null ? universe.getFixtures().size() + 1 : 1), 16);
        txtId.setEnabled(!isEdit);
        JTextField txtName = new JTextField(isEdit ? existing.getName() : "Stage Light Strip", 20);
        JTextField txtGroup = new JTextField(isEdit ? existing.getGroup() : "trusses", 12);
        JComboBox<String> cmbType = new JComboBox<>(new String[]{"linear_strip", "bulb_string", "matrix", "point", "projector"});
        if (isEdit && existing.getType() != null) cmbType.setSelectedItem(existing.getType().toLowerCase());
        JSpinner spnPixels = new JSpinner(new SpinnerNumberModel(isEdit ? existing.getPixelCount() : 300, 1, 10000, 10));
        JComboBox<String> cmbColorOrder = new JComboBox<>(new String[]{"GRB", "RGB", "BRG", "RBG"});
        if (isEdit && existing.getColorOrder() != null) cmbColorOrder.setSelectedItem(existing.getColorOrder());

        // Waypoint coordinates (Start X, Y, Z and End X, Y, Z)
        double sx = 0.0, sy = 0.0, sz = 3.0;
        double ex = 0.0, ey = 0.0, ez = 3.0;
        if (isEdit && !existing.getPoints().isEmpty()) {
            Point3D p0 = existing.getPoints().get(0);
            Point3D pN = existing.getPoints().get(existing.getPoints().size() - 1);
            sx = p0.getX(); sy = p0.getY(); sz = p0.getZ();
            ex = pN.getX(); ey = pN.getY(); ez = pN.getZ();
        }

        JTextField txtStart = new JTextField(String.format("%.1f, %.1f, %.1f", sx, sy, sz), 16);
        JTextField txtEnd = new JTextField(String.format("%.1f, %.1f, %.1f", ex, ey, ez), 16);

        JPanel p = new JPanel(new GridLayout(8, 2, 6, 6));
        p.add(new JLabel("Fixture ID:"));
        p.add(txtId);
        p.add(new JLabel("Name / Label:"));
        p.add(txtName);
        p.add(new JLabel("Group:"));
        p.add(txtGroup);
        p.add(new JLabel("Fixture Type:"));
        p.add(cmbType);
        p.add(new JLabel("Pixel Count:"));
        p.add(spnPixels);
        p.add(new JLabel("Color Order:"));
        p.add(cmbColorOrder);
        p.add(new JLabel("Start Point (X, Y, Z):"));
        p.add(txtStart);
        p.add(new JLabel("End Point (X, Y, Z):"));
        p.add(txtEnd);

        int res = JOptionPane.showConfirmDialog(this, p, isEdit ? "Edit Fixture" : "Add Fixture",
                JOptionPane.OK_CANCEL_OPTION, JOptionPane.PLAIN_MESSAGE);

        if (res == JOptionPane.OK_OPTION) {
            String id = txtId.getText().trim();
            String name = txtName.getText().trim();
            String group = txtGroup.getText().trim();
            String type = (String) cmbType.getSelectedItem();
            int count = (Integer) spnPixels.getValue();
            String colorOrder = (String) cmbColorOrder.getSelectedItem();

            if (id.isEmpty() || name.isEmpty() || group.isEmpty()) {
                JOptionPane.showMessageDialog(this, "ID, Name, and Group are required.", "Validation Error", JOptionPane.ERROR_MESSAGE);
                return;
            }

            // Parse coordinates
            Point3D startPt = parsePoint3D(txtStart.getText().trim(), new Point3D(0, 0, 3));
            Point3D endPt = parsePoint3D(txtEnd.getText().trim(), new Point3D(2, 0, 3));

            FixtureModel target = isEdit ? existing : new FixtureModel();
            target.setId(id);
            target.setName(name);
            target.setGroup(group);
            target.setType(type);
            target.setPixelCount(count);
            target.setColorOrder(colorOrder);
            target.setWaypoints(new ArrayList<>(List.of(startPt, endPt)));
            target.setStart(startPt);
            target.setEnd(endPt);
            target.setOrigin(startPt);
            target.setLocation(startPt);
            target.ensurePixelPointsGenerated();

            if (!isEdit && universe != null) {
                universe.addFixture(target);
            } else if (universe != null) {
                universe.initialize();
            }

            populateFixtureTree();
            selectFixtureInTree(target);
            canvasPanel.repaint();
        }
    }

    private Point3D parsePoint3D(String text, Point3D fallback) {
        try {
            String[] parts = text.split(",");
            if (parts.length >= 3) {
                double x = Double.parseDouble(parts[0].trim());
                double y = Double.parseDouble(parts[1].trim());
                double z = Double.parseDouble(parts[2].trim());
                return new Point3D(x, y, z);
            }
        } catch (Exception ignored) {}
        return fallback;
    }

    private void saveUniverseToFile() {
        if (universe == null) return;
        Path path = universe.getSourcePath();
        if (path == null) {
            path = Paths.get("data", "venue", "universe.json");
        }
        try {
            universe.saveToFile(path);
            JOptionPane.showMessageDialog(this,
                    "Successfully saved Spatial Universe to:\n" + path.toAbsolutePath(),
                    "Universe Saved", JOptionPane.INFORMATION_MESSAGE);
        } catch (IOException ex) {
            JOptionPane.showMessageDialog(this,
                    "Failed to save spatial universe:\n" + ex.getMessage(),
                    "Save Error", JOptionPane.ERROR_MESSAGE);
        }
    }

    private void populateFixtureTree() {
        rootNode.removeAllChildren();
        if (universe == null) return;

        rootNode.setUserObject("Venue Universe (" + universe.getTotalPixels() + " LEDs)");

        List<String> groups = universe.getGroups();
        for (String grp : groups) {
            List<FixtureModel> fixList = universe.getFixturesByGroup(grp);
            int grpPixels = fixList.stream().mapToInt(FixtureModel::getPixelCount).sum();
            DefaultMutableTreeNode groupNode = new DefaultMutableTreeNode(
                    grp.toUpperCase() + " (" + fixList.size() + " fixtures - " + grpPixels + " LEDs)"
            );

            for (FixtureModel f : fixList) {
                groupNode.add(new DefaultMutableTreeNode(new FixtureNodeItem(f)));
            }
            rootNode.add(groupNode);
        }

        treeModel.reload();

        // Expand all group nodes
        for (int i = 0; i < fixtureTree.getRowCount(); i++) {
            fixtureTree.expandRow(i);
        }
    }

    private void selectFixtureInTree(FixtureModel fixture) {
        if (fixture == null) {
            fixtureTree.clearSelection();
            lblDetailName.setText("Select a Fixture");
            lblDetailType.setText("-");
            lblDetailGroup.setText("-");
            lblDetailPixels.setText("-");
            lblDetailController.setText("-");
            lblDetailCoords.setText("-");
            return;
        }

        for (int i = 0; i < rootNode.getChildCount(); i++) {
            DefaultMutableTreeNode grpNode = (DefaultMutableTreeNode) rootNode.getChildAt(i);
            for (int j = 0; j < grpNode.getChildCount(); j++) {
                DefaultMutableTreeNode leaf = (DefaultMutableTreeNode) grpNode.getChildAt(j);
                if (leaf.getUserObject() instanceof FixtureNodeItem item && item.fixture().getId().equals(fixture.getId())) {
                    TreePath path = new TreePath(leaf.getPath());
                    fixtureTree.setSelectionPath(path);
                    fixtureTree.scrollPathToVisible(path);
                    updateDetailsCard(fixture);
                    return;
                }
            }
        }
    }

    private void updateDetailsCard(FixtureModel fixture) {
        if (fixture == null) {
            lblDetailName.setText("Select a Fixture");
            lblDetailType.setText("-");
            lblDetailGroup.setText("-");
            lblDetailPixels.setText("-");
            lblDetailController.setText("-");
            lblDetailCoords.setText("-");
            return;
        }

        lblDetailName.setText(fixture.getName());
        lblDetailType.setText(fixture.getType().toUpperCase());
        lblDetailGroup.setText(fixture.getGroup().toUpperCase());
        lblDetailPixels.setText(String.format("%,d LEDs", fixture.getPixelCount()));

        if (patchTable != null) {
            List<PatchSegmentModel> segs = patchTable.getSegmentsForFixture(fixture.getId());
            if (!segs.isEmpty()) {
                PatchSegmentModel s0 = segs.get(0);
                lblDetailController.setText(s0.getControllerId() + " (CH" + s0.getChannelIndex() + ")");
            } else {
                lblDetailController.setText("Unpatched");
            }
        } else {
            lblDetailController.setText("Patched");
        }

        if (!fixture.getPoints().isEmpty()) {
            Point3D p0 = fixture.getPoints().get(0);
            Point3D pN = fixture.getPoints().get(fixture.getPoints().size() - 1);
            lblDetailCoords.setText(String.format("(%.1f, %.1f) to (%.1f, %.1f)m",
                    p0.getX(), p0.getY(), pN.getX(), pN.getY()));
        } else {
            lblDetailCoords.setText("-");
        }
    }

    private record FixtureNodeItem(FixtureModel fixture) {
        @Override
        public String toString() {
            return fixture.getName() + " [" + fixture.getPixelCount() + " LEDs]";
        }
    }
}
