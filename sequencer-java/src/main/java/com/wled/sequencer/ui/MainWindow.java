package com.wled.sequencer.ui;

import com.wled.sequencer.client.EngineClient;
import com.wled.sequencer.model.SequenceData;
import com.wled.sequencer.model.SequenceDocument;
import com.wled.sequencer.model.SequenceRepository;
import com.wled.sequencer.model.SequenceStep;
import com.wled.sequencer.player.PlayerListener;
import com.wled.sequencer.player.TimelinePlayer;
import com.wled.sequencer.ui.canvas.SpatialStageView;
import com.wled.sequencer.ui.dialogs.SequenceDialogs;
import com.wled.sequencer.ui.fleet.FleetPanel;
import com.wled.sequencer.ui.inspector.InspectorPanel;
import com.wled.sequencer.ui.table.CueTableModel;
import com.wled.sequencer.ui.table.CueTablePanel;
import com.wled.sequencer.ui.transport.TransportPanel;
import com.wled.sequencer.universe.PatchTableModel;
import com.wled.sequencer.universe.SpatialUniverseModel;

import javax.swing.*;
import java.awt.*;
import java.awt.event.InputEvent;
import java.awt.event.KeyEvent;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Set;

/**
 * Main application window for the WLED Universe & Sequence Editor [Java Desktop Edition].
 * Integrates multi-controller universe visualization, hardware fleet monitoring,
 * synchronized property inspection, and hardware-synchronized transport.
 */
public class MainWindow extends JFrame {
    private final SequenceRepository repository;
    private final EngineClient engineClient;
    private final TimelinePlayer player;

    private SpatialUniverseModel universe;
    private PatchTableModel patchTable;

    private SequenceDocument document;

    // Sub-views
    private final CueTableModel tableModel;
    private final CueTablePanel tablePanel;
    private final InspectorPanel inspectorPanel;
    private final TransportPanel transportPanel;
    private final StatusBar statusBar;

    private final SpatialStageView stageView;
    private final FleetPanel fleetPanel;

    // Workspace Containers
    private final JPanel centerContainer = new JPanel(new BorderLayout());
    private final JTabbedPane mainTabs = new JTabbedPane();
    private final JSplitPane splitWorkspace;
    private final JPanel editorWorkspacePanel;
    private boolean isSplitMode = false;

    // Toolbar controls
    private JButton btnToggleSplit;
    private JButton tbBtnPlay;
    private JButton tbBtnPause;
    private JButton tbBtnStop;

    public MainWindow(SequenceRepository repository, EngineClient engineClient,
                      SpatialUniverseModel initialUniverse, PatchTableModel initialPatch) {
        super("WLED Sequence Editor - [Metro Concert Hall]");
        this.repository = repository;
        this.engineClient = engineClient;

        // Load universe and patch models if not provided
        this.universe = initialUniverse != null ? initialUniverse : loadInitialUniverse();
        this.patchTable = initialPatch != null ? initialPatch : loadInitialPatch();

        // Initialize document model and timeline player
        this.document = loadInitialDocument();
        this.player = new TimelinePlayer(engineClient);
        this.player.setSequence(document.getData());

        // Editor Components
        this.tableModel = new CueTableModel(document.getData());
        this.tablePanel = new CueTablePanel(tableModel, player);
        this.inspectorPanel = new InspectorPanel(tableModel);
        this.transportPanel = new TransportPanel(player, engineClient);
        this.statusBar = new StatusBar();

        // Universe & Fleet Views
        this.stageView = new SpatialStageView(universe, patchTable, player);
        this.fleetPanel = new FleetPanel(universe, patchTable, engineClient);

        // Build editor workspace panel (Cue Table + Inspector + Transport HUD)
        this.editorWorkspacePanel = buildEditorWorkspace();

        // Build side-by-side split workspace
        this.splitWorkspace = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT);
        this.splitWorkspace.setResizeWeight(0.52);
        this.splitWorkspace.setDividerSize(6);

        buildUi();
        setupListeners();
        updateDocumentState();

        // Select initial row if available
        if (tableModel.getRowCount() > 0) {
            tablePanel.selectRow(0);
        }

        // Asynchronously discover daemon engine capabilities
        if (engineClient != null) {
            engineClient.fetchCapabilities().thenAccept(inspectorPanel::updateCapabilities);
        }

        setDefaultCloseOperation(JFrame.DO_NOTHING_ON_CLOSE);
        addWindowListener(new WindowAdapter() {
            @Override
            public void windowClosing(WindowEvent e) {
                handleExit();
            }
        });

        setSize(1280, 820);
        setMinimumSize(new Dimension(960, 600));
        setLocationRelativeTo(null);
    }

    public MainWindow(SequenceRepository repository, EngineClient engineClient) {
        this(repository, engineClient, null, null);
    }

    private SpatialUniverseModel loadInitialUniverse() {
        Path p1 = Path.of("data", "venue", "universe.json");
        Path p2 = Path.of("..", "data", "venue", "universe.json");
        Path p = Files.exists(p1) ? p1 : (Files.exists(p2) ? p2 : null);
        if (p != null) {
            try {
                return SpatialUniverseModel.loadFromFile(p);
            } catch (Exception e) {
                System.err.println("Notice: Could not load universe from " + p + ": " + e.getMessage());
            }
        }
        SpatialUniverseModel def = new SpatialUniverseModel();
        def.setName("Metro Concert Hall & Lounge");
        def.setSourcePath(p1);
        return def;
    }

    private PatchTableModel loadInitialPatch() {
        Path p1 = Path.of("data", "venue", "patch.json");
        Path p2 = Path.of("..", "data", "venue", "patch.json");
        Path p = Files.exists(p1) ? p1 : (Files.exists(p2) ? p2 : null);
        if (p != null) {
            try {
                return PatchTableModel.loadFromFile(p);
            } catch (Exception e) {
                System.err.println("Notice: Could not load patch from " + p + ": " + e.getMessage());
            }
        }
        PatchTableModel def = new PatchTableModel();
        def.setSourcePath(p1);
        return def;
    }

    private SequenceDocument loadInitialDocument() {
        SequenceData demo = repository.loadSequence("garage_light_show.json");
        if (demo != null) {
            return new SequenceDocument(demo, "garage_light_show.json");
        }
        SequenceData def = new SequenceData("Metro Concert Hall Opening Show");
        SequenceStep s1 = new SequenceStep("s1", "Ambient Ocean Wash", "Intro", 0, 0.0, 10.0, "wave");
        s1.setFixtureGroup("all");
        def.getSteps().add(s1);
        return new SequenceDocument(def, "untitled.json");
    }

    private JPanel buildEditorWorkspace() {
        JPanel p = new JPanel(new BorderLayout(4, 4));

        // Center Split: Cue Table (Left) and Inspector (Right)
        JSplitPane splitPane = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT, tablePanel, inspectorPanel);
        splitPane.setResizeWeight(0.56);
        splitPane.setDividerSize(6);
        splitPane.setBorder(BorderFactory.createEmptyBorder(4, 6, 4, 6));

        // Bottom HUD container: Transport Panel + Status Bar
        JPanel bottomContainer = new JPanel(new BorderLayout(4, 4));
        bottomContainer.setBorder(BorderFactory.createEmptyBorder(0, 6, 4, 6));
        bottomContainer.add(transportPanel, BorderLayout.CENTER);
        bottomContainer.add(statusBar, BorderLayout.SOUTH);

        p.add(splitPane, BorderLayout.CENTER);
        p.add(bottomContainer, BorderLayout.SOUTH);

        return p;
    }

    private void buildUi() {
        setLayout(new BorderLayout(4, 4));

        // Menu Bar
        setJMenuBar(createMenuBar());

        // Top Toolbar
        add(createToolBar(), BorderLayout.NORTH);

        // Center Workspace (starts in Tabbed Mode)
        mainTabs.addTab("Timeline & Cues", editorWorkspacePanel);
        mainTabs.addTab("Spatial Stage Universe", stageView);
        mainTabs.addTab("Controller Fleet (20 Nodes)", fleetPanel);

        centerContainer.add(mainTabs, BorderLayout.CENTER);
        add(centerContainer, BorderLayout.CENTER);
    }

    private void setWorkspaceMode(boolean split) {
        this.isSplitMode = split;
        centerContainer.removeAll();

        if (split) {
            splitWorkspace.setLeftComponent(editorWorkspacePanel);
            splitWorkspace.setRightComponent(stageView);
            centerContainer.add(splitWorkspace, BorderLayout.CENTER);
            if (btnToggleSplit != null) btnToggleSplit.setText("Tabbed View");
            stageView.getCanvasPanel().fitView();
        } else {
            mainTabs.removeAll();
            mainTabs.addTab("Timeline & Cues", editorWorkspacePanel);
            mainTabs.addTab("Spatial Stage Universe", stageView);
            mainTabs.addTab("Controller Fleet (20 Nodes)", fleetPanel);
            centerContainer.add(mainTabs, BorderLayout.CENTER);
            if (btnToggleSplit != null) btnToggleSplit.setText("Split Live View");
        }

        centerContainer.revalidate();
        centerContainer.repaint();
    }

    private JMenuBar createMenuBar() {
        JMenuBar mb = new JMenuBar();
        int shortcutMask = Toolkit.getDefaultToolkit().getMenuShortcutKeyMaskEx();

        // --- File Menu ---
        JMenu menuFile = new JMenu("File");
        JMenuItem miNew = new JMenuItem("New Sequence");
        miNew.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_N, shortcutMask));
        miNew.addActionListener(e -> newSequence());

        JMenuItem miOpen = new JMenuItem("Open Sequence...");
        miOpen.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_O, shortcutMask));
        miOpen.addActionListener(e -> openSequence());

        JMenuItem miSave = new JMenuItem("Save");
        miSave.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_S, shortcutMask));
        miSave.addActionListener(e -> saveSequence());

        JMenuItem miSaveAs = new JMenuItem("Save As...");
        miSaveAs.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_S, shortcutMask | InputEvent.SHIFT_DOWN_MASK));
        miSaveAs.addActionListener(e -> saveSequenceAs());

        JMenuItem miExit = new JMenuItem("Exit");
        miExit.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_Q, shortcutMask));
        miExit.addActionListener(e -> handleExit());

        menuFile.add(miNew);
        menuFile.add(miOpen);
        menuFile.addSeparator();
        menuFile.add(miSave);
        menuFile.add(miSaveAs);
        menuFile.addSeparator();
        menuFile.add(miExit);

        // --- Edit Menu ---
        JMenu menuEdit = new JMenu("Edit");
        JMenuItem miAdd = new JMenuItem("Add Step");
        miAdd.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_N, shortcutMask | InputEvent.SHIFT_DOWN_MASK));
        miAdd.addActionListener(e -> tablePanel.addNewStep());

        JMenuItem miDup = new JMenuItem("Duplicate Selected Step");
        miDup.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_D, shortcutMask));
        miDup.addActionListener(e -> tablePanel.duplicateSelectedStep());

        JMenuItem miDel = new JMenuItem("Delete Selected Step");
        miDel.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_BACK_SPACE, shortcutMask));
        miDel.addActionListener(e -> tablePanel.deleteSelectedStep());

        JMenuItem miMoveUp = new JMenuItem("Move Step Up");
        miMoveUp.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_UP, InputEvent.ALT_DOWN_MASK));
        miMoveUp.addActionListener(e -> tablePanel.moveStepUp());

        JMenuItem miMoveDown = new JMenuItem("Move Step Down");
        miMoveDown.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_DOWN, InputEvent.ALT_DOWN_MASK));
        miMoveDown.addActionListener(e -> tablePanel.moveStepDown());

        menuEdit.add(miAdd);
        menuEdit.add(miDup);
        menuEdit.add(miDel);
        menuEdit.addSeparator();
        menuEdit.add(miMoveUp);
        menuEdit.add(miMoveDown);

        // --- View Menu ---
        JMenu menuView = new JMenu("View");
        JMenuItem miTabTimeline = new JMenuItem("Timeline & Cues View");
        miTabTimeline.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_1, shortcutMask));
        miTabTimeline.addActionListener(e -> {
            if (isSplitMode) setWorkspaceMode(false);
            mainTabs.setSelectedIndex(0);
        });

        JMenuItem miTabStage = new JMenuItem("Spatial Stage Universe View");
        miTabStage.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_2, shortcutMask));
        miTabStage.addActionListener(e -> {
            if (isSplitMode) setWorkspaceMode(false);
            mainTabs.setSelectedIndex(1);
            stageView.getCanvasPanel().fitView();
        });

        JMenuItem miTabFleet = new JMenuItem("Controller Fleet & Patch (20 Nodes)");
        miTabFleet.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_3, shortcutMask));
        miTabFleet.addActionListener(e -> {
            if (isSplitMode) setWorkspaceMode(false);
            mainTabs.setSelectedIndex(2);
        });

        JMenuItem miToggleSplit = new JMenuItem("Toggle Side-by-Side Split View");
        miToggleSplit.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_4, shortcutMask));
        miToggleSplit.addActionListener(e -> setWorkspaceMode(!isSplitMode));

        JMenuItem miFitStage = new JMenuItem("Fit Stage to View");
        miFitStage.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_F, 0));
        miFitStage.addActionListener(e -> stageView.getCanvasPanel().fitView());

        menuView.add(miTabTimeline);
        menuView.add(miTabStage);
        menuView.add(miTabFleet);
        menuView.addSeparator();
        menuView.add(miToggleSplit);
        menuView.add(miFitStage);

        // --- Transport Menu ---
        JMenu menuTransport = new JMenu("Transport");
        JMenuItem miPlay = new JMenuItem("Play on Engine");
        miPlay.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_R, shortcutMask));
        miPlay.addActionListener(e -> player.play());

        JMenuItem miPause = new JMenuItem("Pause");
        miPause.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_P, shortcutMask));
        miPause.addActionListener(e -> player.pause());

        JMenuItem miStop = new JMenuItem("Stop Playback");
        miStop.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_ESCAPE, 0));
        miStop.addActionListener(e -> {
            player.stop();
            if (stageView != null) {
                stageView.resetTimeline();
            }
        });

        JMenuItem miBlackout = new JMenuItem("Blackout All Controllers");
        miBlackout.addActionListener(e -> {
            player.stop();
            if (engineClient != null) {
                engineClient.blackout();
            }
            if (stageView != null) {
                stageView.blackout();
            }
        });

        menuTransport.add(miPlay);
        menuTransport.add(miPause);
        menuTransport.add(miStop);
        menuTransport.addSeparator();
        menuTransport.add(miBlackout);

        // --- Help Menu ---
        JMenu menuHelp = new JMenu("Help");
        JMenuItem miAbout = new JMenuItem("About WLED Sequence Editor");
        miAbout.addActionListener(e -> SequenceDialogs.showAboutDialog(this));
        menuHelp.add(miAbout);

        mb.add(menuFile);
        mb.add(menuEdit);
        mb.add(menuView);
        mb.add(menuTransport);
        mb.add(menuHelp);

        return mb;
    }

    private JToolBar createToolBar() {
        JToolBar tb = new JToolBar();
        tb.setFloatable(false);
        tb.setBorder(BorderFactory.createMatteBorder(0, 0, 1, 0, new Color(215, 215, 215)));

        // Document Authoring Group
        JButton btnNew = new JButton("New");
        JButton btnOpen = new JButton("Open");
        JButton btnSave = new JButton("Save");

        btnNew.setToolTipText("Create a new sequence document (Ctrl+N)");
        btnOpen.setToolTipText("Open an existing sequence (Ctrl+O)");
        btnSave.setToolTipText("Save sequence to disk (Ctrl+S)");

        btnNew.addActionListener(e -> newSequence());
        btnOpen.addActionListener(e -> openSequence());
        btnSave.addActionListener(e -> saveSequence());

        tb.add(btnNew);
        tb.add(btnOpen);
        tb.add(btnSave);

        tb.addSeparator(new Dimension(14, 24));

        // Step Authoring Group
        JButton btnAddStep = new JButton("Add Step");
        JButton btnDupStep = new JButton("Duplicate");
        JButton btnDelStep = new JButton("Delete");
        JButton btnMoveUp = new JButton("Move Up");
        JButton btnMoveDown = new JButton("Move Down");

        btnAddStep.setToolTipText("Add a new cue step (Shift+Ctrl+N)");
        btnDupStep.setToolTipText("Duplicate selected cue step (Ctrl+D)");
        btnDelStep.setToolTipText("Delete selected cue step (Delete)");
        btnMoveUp.setToolTipText("Move cue step up earlier in timeline (Alt+Up)");
        btnMoveDown.setToolTipText("Move cue step down later in timeline (Alt+Down)");

        btnAddStep.addActionListener(e -> tablePanel.addNewStep());
        btnDupStep.addActionListener(e -> tablePanel.duplicateSelectedStep());
        btnDelStep.addActionListener(e -> tablePanel.deleteSelectedStep());
        btnMoveUp.addActionListener(e -> tablePanel.moveStepUp());
        btnMoveDown.addActionListener(e -> tablePanel.moveStepDown());

        tb.add(btnAddStep);
        tb.add(btnDupStep);
        tb.add(btnDelStep);
        tb.add(btnMoveUp);
        tb.add(btnMoveDown);

        tb.addSeparator(new Dimension(14, 24));

        // Remote Engine Transport Group
        tbBtnPlay = new JButton("Play");
        tbBtnPause = new JButton("Pause");
        tbBtnStop = new JButton("Stop");
        JButton btnBlackout = new JButton("Blackout");

        tbBtnPlay.setToolTipText("Start playback on engine (Space or Ctrl+R)");
        tbBtnPause.setToolTipText("Pause playback on engine (Space or Ctrl+P)");
        tbBtnStop.setToolTipText("Stop playback and reset layers (Esc)");
        btnBlackout.setToolTipText("Immediately turn off all LEDs on engine");

        tbBtnPlay.addActionListener(e -> player.play());
        tbBtnPause.addActionListener(e -> player.pause());
        tbBtnStop.addActionListener(e -> {
            player.stop();
            if (stageView != null) {
                stageView.resetTimeline();
            }
        });
        btnBlackout.addActionListener(e -> {
            player.stop();
            if (engineClient != null) {
                engineClient.blackout();
            }
            if (stageView != null) {
                stageView.blackout();
            }
        });

        tb.add(tbBtnPlay);
        tb.add(tbBtnPause);
        tb.add(tbBtnStop);
        tb.add(btnBlackout);

        tb.addSeparator(new Dimension(16, 24));

        // View Mode Group
        JButton btnViewTimeline = new JButton("Timeline");
        JButton btnViewStage = new JButton("Stage");
        JButton btnViewFleet = new JButton("Fleet");
        btnToggleSplit = new JButton("Split Live View");

        btnViewTimeline.addActionListener(e -> {
            if (isSplitMode) setWorkspaceMode(false);
            mainTabs.setSelectedIndex(0);
        });

        btnViewStage.addActionListener(e -> {
            if (isSplitMode) setWorkspaceMode(false);
            mainTabs.setSelectedIndex(1);
            stageView.getCanvasPanel().fitView();
        });

        btnViewFleet.addActionListener(e -> {
            if (isSplitMode) setWorkspaceMode(false);
            mainTabs.setSelectedIndex(2);
        });

        btnToggleSplit.addActionListener(e -> setWorkspaceMode(!isSplitMode));

        tb.add(btnViewTimeline);
        tb.add(btnViewStage);
        tb.add(btnViewFleet);
        tb.add(btnToggleSplit);

        updateToolbarButtons(player.isPlaying(), player.isPaused());

        return tb;
    }

    private void updateToolbarButtons(boolean isPlaying, boolean isPaused) {
        if (tbBtnPlay != null) tbBtnPlay.setEnabled(!isPlaying || isPaused);
        if (tbBtnPause != null) tbBtnPause.setEnabled(isPlaying && !isPaused);
        if (tbBtnStop != null) tbBtnStop.setEnabled(isPlaying || isPaused);
    }

    private void setupListeners() {
        // Table selection -> Inspector
        tablePanel.setOnStepSelected(step -> {
            int row = tablePanel.getTable().getSelectedRow();
            inspectorPanel.setStep(step, row);
        });

        // Table / Inspector modifications mark document dirty
        tableModel.setOnModifiedCallback(() -> document.markDirty());

        // Document state changes -> Update window title & status bar
        document.addListener(doc -> updateDocumentState());

        // Spacebar toggles Play/Pause across the entire window (unless typing in text components)
        getRootPane().getInputMap(JComponent.WHEN_IN_FOCUSED_WINDOW).put(
                KeyStroke.getKeyStroke(KeyEvent.VK_SPACE, 0), "togglePlayPause"
        );
        getRootPane().getActionMap().put("togglePlayPause", new AbstractAction() {
            @Override
            public void actionPerformed(java.awt.event.ActionEvent e) {
                Component focus = KeyboardFocusManager.getCurrentKeyboardFocusManager().getFocusOwner();
                if (focus instanceof javax.swing.text.JTextComponent) {
                    return;
                }
                if (player.isPlaying() && !player.isPaused()) {
                    player.pause();
                } else {
                    player.play();
                }
            }
        });

        // Escape stops playback
        getRootPane().getInputMap(JComponent.WHEN_IN_FOCUSED_WINDOW).put(
                KeyStroke.getKeyStroke(KeyEvent.VK_ESCAPE, 0), "stopPlayback"
        );
        getRootPane().getActionMap().put("stopPlayback", new AbstractAction() {
            @Override
            public void actionPerformed(java.awt.event.ActionEvent e) {
                player.stop();
            }
        });

        // Player transport listeners
        player.addListener(new PlayerListener() {
            @Override
            public void onPlaybackTick(double elapsedSec, double totalDurationSec, int activeCount) {
                SwingUtilities.invokeLater(() -> {
                    statusBar.setTotalDuration(totalDurationSec);
                    statusBar.setCueCount(document.getData().getSteps().size());
                });
            }

            @Override
            public void onActiveCuesChanged(Set<String> activeCueIds) {
                SwingUtilities.invokeLater(() -> {
                    if (player.isPlaying()) {
                        statusBar.setStatus("Playing (" + activeCueIds.size() + " concurrent cues active across universe)");
                    }
                });
            }

            @Override
            public void onPlaybackStateChanged(boolean isPlaying, boolean isPaused) {
                SwingUtilities.invokeLater(() -> {
                    if (isPlaying) {
                        statusBar.setStatus(isPaused ? "Playback Paused" : "Playing Timeline (20 Nodes Synced)");
                    } else {
                        statusBar.setStatus("Stopped (Ready - 28 Fixtures Patched)");
                        if (stageView != null) {
                            stageView.resetTimeline();
                        }
                    }
                    updateToolbarButtons(isPlaying, isPaused);
                });
            }
        });
    }

    private void updateDocumentState() {
        String baseName = document.getFilename() != null && !document.getFilename().isBlank()
                ? document.getFilename()
                : document.getData().getName();
        if (baseName == null || baseName.isBlank()) {
            baseName = "Untitled";
        }
        String dirtyMarker = document.isDirty() ? " *" : "";
        setTitle("WLED Sequence Editor - [" + baseName + dirtyMarker + "] - " + universe.getName());

        statusBar.setDocumentDirty(document.isDirty());
        statusBar.setCueCount(document.getData().getSteps().size());
        statusBar.setTotalDuration(document.getData().getTotalDuration());
    }

    private boolean promptSaveIfDirty() {
        if (!document.isDirty()) {
            return true;
        }

        String docName = document.getFilename() != null ? document.getFilename() : document.getData().getName();
        int choice = JOptionPane.showConfirmDialog(
                this,
                "The sequence \"" + docName + "\" has unsaved modifications.\nDo you want to save changes before continuing?",
                "Unsaved Changes",
                JOptionPane.YES_NO_CANCEL_OPTION,
                JOptionPane.WARNING_MESSAGE
        );

        if (choice == JOptionPane.YES_OPTION) {
            return saveSequence();
        } else if (choice == JOptionPane.NO_OPTION) {
            return true; // Discard changes
        } else {
            return false; // Cancel action
        }
    }

    private void handleExit() {
        if (promptSaveIfDirty()) {
            player.stop();
            dispose();
            System.exit(0);
        }
    }

    private void newSequence() {
        if (!promptSaveIfDirty()) return;

        player.stop();
        SequenceData newData = new SequenceData("Untitled Sequence");
        document.setData(newData, "untitled.json");
        tableModel.setSequence(document.getData());
        player.setSequence(document.getData());
        updateDocumentState();

        if (tableModel.getRowCount() > 0) {
            tablePanel.selectRow(0);
        } else {
            inspectorPanel.setStep(null, -1);
        }
    }

    private void openSequence() {
        if (!promptSaveIfDirty()) return;

        SequenceDialogs.SelectedSequence selected = SequenceDialogs.showOpenSequenceDialog(this, repository);
        if (selected != null && selected.data() != null) {
            player.stop();
            document.setData(selected.data(), selected.filename());
            tableModel.setSequence(document.getData());
            player.setSequence(document.getData());
            updateDocumentState();

            if (tableModel.getRowCount() > 0) {
                tablePanel.selectRow(0);
            } else {
                inspectorPanel.setStep(null, -1);
            }
        }
    }

    private boolean saveSequence() {
        String fname = document.getFilename();
        if (fname == null || fname.isBlank() || "untitled.json".equalsIgnoreCase(fname)) {
            return saveSequenceAs();
        }

        try {
            String saved = repository.saveSequence(document.getData(), fname);
            document.setFilename(saved);
            document.markClean();
            statusBar.setStatus("Sequence saved to " + saved);
            return true;
        } catch (IOException e) {
            JOptionPane.showMessageDialog(this, "Failed to save sequence: " + e.getMessage(),
                    "Error", JOptionPane.ERROR_MESSAGE);
            return false;
        }
    }

    private boolean saveSequenceAs() {
        String defaultName = document.getFilename();
        if (defaultName != null && defaultName.endsWith(".json")) {
            defaultName = defaultName.substring(0, defaultName.length() - 5);
        }
        if (defaultName == null || defaultName.isBlank()) {
            defaultName = document.getData().getName();
        }

        String newName = SequenceDialogs.showSaveAsDialog(this, defaultName);
        if (newName != null && !newName.isBlank()) {
            document.getData().setName(newName);
            String safeFile = newName.toLowerCase().replaceAll("[^a-z0-9_\\-]", "_");
            if (!safeFile.endsWith(".json")) {
                safeFile += ".json";
            }
            try {
                String saved = repository.saveSequence(document.getData(), safeFile);
                document.setFilename(saved);
                document.markClean();
                statusBar.setStatus("Sequence saved as " + saved);
                return true;
            } catch (IOException e) {
                JOptionPane.showMessageDialog(this, "Failed to save sequence: " + e.getMessage(),
                        "Error", JOptionPane.ERROR_MESSAGE);
                return false;
            }
        }
        return false;
    }
}
