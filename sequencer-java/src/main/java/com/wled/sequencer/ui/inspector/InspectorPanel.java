package com.wled.sequencer.ui.inspector;

import com.wled.sequencer.model.SequenceStep;
import com.wled.sequencer.ui.table.CueTableModel;
import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.util.ArrayList;
import java.util.List;

/**
 * Property inspector with General, Pattern, and Timing tabs featuring two-way synchronization.
 */
public class InspectorPanel extends JPanel {
    private final CueTableModel tableModel;
    private SequenceStep currentStep = null;
    private int currentRow = -1;
    private boolean isPopulating = false;

    // Tab 1: General & Layer
    private final JTextField txtSection = new JTextField(10);
    private final JComboBox<String> cmbQuickSection = new JComboBox<>(new String[]{
            "Quick Pick...", "Intro", "Verse", "Chorus", "Bridge", "Drop", "Build-Up", "Main Drive", "Twilight", "Outro"
    });
    private final JTextField txtName = new JTextField(14);
    private final JComboBox<String> cmbLayer = new JComboBox<>();
    private final JComboBox<String> cmbBlend = new JComboBox<>(new String[]{
            "OVERWRITE", "ALPHA_BLEND", "ADDITIVE", "MULTIPLY", "MAX", "MASK"
    });
    private final JComboBox<String> cmbFixtureGroup = new JComboBox<>(new String[]{
            "All Fixtures", "Trusses", "Festoon", "Panels", "Lamps", "Projectors"
    });
    private final JCheckBox chkChAll = new JCheckBox("All", true);
    private final JCheckBox chkCh1 = new JCheckBox("CH1");
    private final JCheckBox chkCh2 = new JCheckBox("CH2");
    private final JCheckBox chkCh3 = new JCheckBox("CH3");
    private final JCheckBox chkCh4 = new JCheckBox("CH4");

    // Tab 2: Pattern & Color
    private final JComboBox<String> cmbPattern = new JComboBox<>(new String[]{
            "rainbow", "chase", "fire", "meteor", "cylon", "twinkle", "wave", "gradient", "blink", "wipe", "solid", "none"
    });
    private final JTextField txtColorHex = new JTextField("#FF0000", 7);
    private final JButton btnColorPick = new JButton("   ");
    private final JComboBox<String> cmbPalette = new JComboBox<>(new String[]{
            "(None / Solid Primary)", "cyberpunk", "sunset", "ocean", "forest", "fire", "police", "party"
    });
    private final JSlider sldSpeed = new JSlider(1, 50, 10);
    private final JSpinner spnSpeed = new JSpinner(new SpinnerNumberModel(1.0, 0.1, 10.0, 0.1));
    private final JSlider sldBrightness = new JSlider(0, 100, 100);
    private final JSpinner spnBrightness = new JSpinner(new SpinnerNumberModel(1.0, 0.0, 1.0, 0.05));

    // Tab 3: Timing & Fade
    private final JSpinner spnStart = new JSpinner(new SpinnerNumberModel(0.0, 0.0, 3600.0, 0.5));
    private final JSpinner spnDuration = new JSpinner(new SpinnerNumberModel(4.0, 0.1, 3600.0, 0.5));
    private final JSpinner spnStop = new JSpinner(new SpinnerNumberModel(4.0, 0.1, 3600.0, 0.5));
    private final JSpinner spnTransition = new JSpinner(new SpinnerNumberModel(1.0, 0.0, 60.0, 0.1));
    private final JSpinner spnFadeOut = new JSpinner(new SpinnerNumberModel(0.5, 0.0, 60.0, 0.1));
    private final JSlider sldOpacity = new JSlider(0, 100, 100);
    private final JSpinner spnOpacity = new JSpinner(new SpinnerNumberModel(1.0, 0.0, 1.0, 0.05));

    public InspectorPanel(CueTableModel tableModel) {
        this.tableModel = tableModel;

        setLayout(new BorderLayout());
        setBorder(BorderFactory.createTitledBorder("Step Property Inspector"));

        JTabbedPane tabbedPane = new JTabbedPane();
        tabbedPane.addTab("General & Layer", createGeneralTab());
        tabbedPane.addTab("Pattern & Color", createPatternTab());
        tabbedPane.addTab("Timing & Fade", createTimingTab());

        add(tabbedPane, BorderLayout.CENTER);

        setupEventBindings();
        setEnabledAll(false);
    }

    public void setStep(SequenceStep step, int row) {
        this.currentStep = step;
        this.currentRow = row;
        if (step == null) {
            setEnabledAll(false);
            return;
        }

        setEnabledAll(true);
        isPopulating = true;

        // General
        txtSection.setText(step.getSection() != null ? step.getSection() : "Main");
        txtName.setText(step.getName() != null ? step.getName() : "Cue");
        cmbLayer.setSelectedIndex(step.getTargetLayer());
        cmbBlend.setSelectedItem(step.getBlendMode());

        String grp = step.getFixtureGroup();
        if ("trusses".equalsIgnoreCase(grp)) cmbFixtureGroup.setSelectedIndex(1);
        else if ("festoon".equalsIgnoreCase(grp)) cmbFixtureGroup.setSelectedIndex(2);
        else if ("panels".equalsIgnoreCase(grp)) cmbFixtureGroup.setSelectedIndex(3);
        else if ("lamps".equalsIgnoreCase(grp)) cmbFixtureGroup.setSelectedIndex(4);
        else if ("projectors".equalsIgnoreCase(grp)) cmbFixtureGroup.setSelectedIndex(5);
        else cmbFixtureGroup.setSelectedIndex(0);

        List<Integer> chs = step.getChannels();
        if (chs == null || chs.isEmpty()) {
            chkChAll.setSelected(true);
            chkCh1.setSelected(false);
            chkCh2.setSelected(false);
            chkCh3.setSelected(false);
            chkCh4.setSelected(false);
        } else {
            chkChAll.setSelected(false);
            chkCh1.setSelected(chs.contains(1));
            chkCh2.setSelected(chs.contains(2));
            chkCh3.setSelected(chs.contains(3));
            chkCh4.setSelected(chs.contains(4));
        }

        // Pattern
        cmbPattern.setSelectedItem(step.getPatternId());
        txtColorHex.setText(step.getPrimaryColor());
        updateColorButtonBackground(step.getPrimaryColor());
        cmbPalette.setSelectedItem(step.getPalette() != null ? step.getPalette() : "(None / Solid Primary)");

        spnSpeed.setValue(step.getSpeed());
        sldSpeed.setValue((int) (step.getSpeed() * 10));

        spnBrightness.setValue(step.getBrightness());
        sldBrightness.setValue((int) (step.getBrightness() * 100));

        // Timing
        spnStart.setValue(step.getStartTimeSec());
        spnDuration.setValue(step.getDurationSec());
        spnStop.setValue(step.getStopTimeSec());
        spnTransition.setValue(step.getTransitionSec());
        spnFadeOut.setValue(step.getFadeOutSec());

        spnOpacity.setValue(step.getTargetOpacity());
        sldOpacity.setValue((int) (step.getTargetOpacity() * 100));

        isPopulating = false;
    }

    private JPanel createGeneralTab() {
        JPanel p = new JPanel(new GridBagLayout());
        p.setBorder(new EmptyBorder(8, 8, 8, 8));

        GridBagConstraints g = new GridBagConstraints();
        g.insets = new Insets(3, 4, 3, 4);
        g.anchor = GridBagConstraints.WEST;
        g.fill = GridBagConstraints.HORIZONTAL;

        // Populate layer combo with generic numerals (0..9)
        for (int i = 0; i < 10; i++) {
            cmbLayer.addItem("Layer " + i);
        }

        // Section
        g.gridx = 0; g.gridy = 0;
        p.add(new JLabel("Section:"), g);
        g.gridx = 1;
        JPanel secPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 2, 0));
        secPanel.add(txtSection);
        secPanel.add(cmbQuickSection);
        p.add(secPanel, g);

        // Name
        g.gridx = 0; g.gridy = 1;
        p.add(new JLabel("Cue Name:"), g);
        g.gridx = 1;
        p.add(txtName, g);

        // Layer
        g.gridx = 0; g.gridy = 2;
        p.add(new JLabel("Target Layer:"), g);
        g.gridx = 1;
        p.add(cmbLayer, g);

        // Blend
        g.gridx = 0; g.gridy = 3;
        p.add(new JLabel("Blend Mode:"), g);
        g.gridx = 1;
        p.add(cmbBlend, g);

        // Fixture Group
        g.gridx = 0; g.gridy = 4;
        p.add(new JLabel("Fixture Group:"), g);
        g.gridx = 1;
        p.add(cmbFixtureGroup, g);

        // Channels
        g.gridx = 0; g.gridy = 5;
        p.add(new JLabel("Channel Mask:"), g);
        g.gridx = 1;
        JPanel chPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 4, 0));
        chPanel.add(chkChAll);
        chPanel.add(chkCh1);
        chPanel.add(chkCh2);
        chPanel.add(chkCh3);
        chPanel.add(chkCh4);
        p.add(chPanel, g);

        return p;
    }

    private JPanel createPatternTab() {
        JPanel p = new JPanel(new GridBagLayout());
        p.setBorder(new EmptyBorder(8, 8, 8, 8));

        GridBagConstraints g = new GridBagConstraints();
        g.insets = new Insets(3, 4, 3, 4);
        g.anchor = GridBagConstraints.WEST;
        g.fill = GridBagConstraints.HORIZONTAL;

        // Pattern
        g.gridx = 0; g.gridy = 0;
        p.add(new JLabel("Pattern FX:"), g);
        g.gridx = 1;
        p.add(cmbPattern, g);

        // Color
        g.gridx = 0; g.gridy = 1;
        p.add(new JLabel("Primary Color:"), g);
        g.gridx = 1;
        JPanel colPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 4, 0));
        btnColorPick.setPreferredSize(new Dimension(30, 22));
        colPanel.add(txtColorHex);
        colPanel.add(btnColorPick);
        p.add(colPanel, g);

        // Palette
        g.gridx = 0; g.gridy = 2;
        p.add(new JLabel("Color Palette:"), g);
        g.gridx = 1;
        p.add(cmbPalette, g);

        // Speed
        g.gridx = 0; g.gridy = 3;
        p.add(new JLabel("Speed:"), g);
        g.gridx = 1;
        JPanel spdPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 4, 0));
        spdPanel.add(sldSpeed);
        spdPanel.add(spnSpeed);
        p.add(spdPanel, g);

        // Brightness
        g.gridx = 0; g.gridy = 4;
        p.add(new JLabel("Brightness:"), g);
        g.gridx = 1;
        JPanel briPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 4, 0));
        briPanel.add(sldBrightness);
        briPanel.add(spnBrightness);
        p.add(briPanel, g);

        return p;
    }

    private JPanel createTimingTab() {
        JPanel p = new JPanel(new GridBagLayout());
        p.setBorder(new EmptyBorder(8, 8, 8, 8));

        GridBagConstraints g = new GridBagConstraints();
        g.insets = new Insets(3, 4, 3, 4);
        g.anchor = GridBagConstraints.WEST;
        g.fill = GridBagConstraints.HORIZONTAL;

        // Start Time
        g.gridx = 0; g.gridy = 0;
        p.add(new JLabel("Start Time (s):"), g);
        g.gridx = 1;
        p.add(spnStart, g);

        // Duration
        g.gridx = 0; g.gridy = 1;
        p.add(new JLabel("Duration (s):"), g);
        g.gridx = 1;
        p.add(spnDuration, g);

        // Stop Time
        g.gridx = 0; g.gridy = 2;
        p.add(new JLabel("Stop Time (s):"), g);
        g.gridx = 1;
        p.add(spnStop, g);

        // Fade In
        g.gridx = 0; g.gridy = 3;
        p.add(new JLabel("Fade In (s):"), g);
        g.gridx = 1;
        p.add(spnTransition, g);

        // Fade Out
        g.gridx = 0; g.gridy = 4;
        p.add(new JLabel("Fade Out (s):"), g);
        g.gridx = 1;
        p.add(spnFadeOut, g);

        // Opacity
        g.gridx = 0; g.gridy = 5;
        p.add(new JLabel("Opacity:"), g);
        g.gridx = 1;
        JPanel opPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 4, 0));
        opPanel.add(sldOpacity);
        opPanel.add(spnOpacity);
        p.add(opPanel, g);

        return p;
    }

    private void setupEventBindings() {
        // Quick section picker
        cmbQuickSection.addActionListener(e -> {
            if (isPopulating || cmbQuickSection.getSelectedIndex() <= 0) return;
            txtSection.setText((String) cmbQuickSection.getSelectedItem());
            cmbQuickSection.setSelectedIndex(0);
            saveToStep();
        });

        // Text & combos
        txtSection.addActionListener(e -> saveToStep());
        txtName.addActionListener(e -> saveToStep());
        cmbLayer.addActionListener(e -> saveToStep());
        cmbBlend.addActionListener(e -> saveToStep());
        cmbFixtureGroup.addActionListener(e -> saveToStep());
        cmbPattern.addActionListener(e -> saveToStep());
        cmbPalette.addActionListener(e -> saveToStep());

        // Channel checkboxes
        chkChAll.addActionListener(e -> {
            if (isPopulating) return;
            if (chkChAll.isSelected()) {
                chkCh1.setSelected(false);
                chkCh2.setSelected(false);
                chkCh3.setSelected(false);
                chkCh4.setSelected(false);
            }
            saveToStep();
        });

        JCheckBox[] channelBoxes = {chkCh1, chkCh2, chkCh3, chkCh4};
        for (JCheckBox cb : channelBoxes) {
            cb.addActionListener(e -> {
                if (isPopulating) return;
                if (cb.isSelected()) {
                    chkChAll.setSelected(false);
                }
                saveToStep();
            });
        }

        // Color chooser
        btnColorPick.addActionListener(e -> {
            Color init = parseColor(txtColorHex.getText());
            Color chosen = JColorChooser.showDialog(this, "Select Primary Color", init);
            if (chosen != null) {
                String hex = String.format("#%02X%02X%02X", chosen.getRed(), chosen.getGreen(), chosen.getBlue());
                txtColorHex.setText(hex);
                updateColorButtonBackground(hex);
                saveToStep();
            }
        });

        txtColorHex.addActionListener(e -> {
            updateColorButtonBackground(txtColorHex.getText());
            saveToStep();
        });

        // Sliders & Spinners
        sldSpeed.addChangeListener(e -> {
            if (isPopulating) return;
            spnSpeed.setValue(sldSpeed.getValue() / 10.0);
            saveToStep();
        });
        spnSpeed.addChangeListener(e -> {
            if (isPopulating) return;
            sldSpeed.setValue((int) (((Double) spnSpeed.getValue()) * 10));
            saveToStep();
        });

        sldBrightness.addChangeListener(e -> {
            if (isPopulating) return;
            spnBrightness.setValue(sldBrightness.getValue() / 100.0);
            saveToStep();
        });
        spnBrightness.addChangeListener(e -> {
            if (isPopulating) return;
            sldBrightness.setValue((int) (((Double) spnBrightness.getValue()) * 100));
            saveToStep();
        });

        sldOpacity.addChangeListener(e -> {
            if (isPopulating) return;
            spnOpacity.setValue(sldOpacity.getValue() / 100.0);
            saveToStep();
        });
        spnOpacity.addChangeListener(e -> {
            if (isPopulating) return;
            sldOpacity.setValue((int) (((Double) spnOpacity.getValue()) * 100));
            saveToStep();
        });

        // Two-way calculation for timing
        spnStart.addChangeListener(e -> {
            if (isPopulating) return;
            double s = (Double) spnStart.getValue();
            double d = (Double) spnDuration.getValue();
            double stop = Math.round((s + d) * 10.0) / 10.0;
            spnStop.setValue(stop);
            saveToStep();
        });

        spnDuration.addChangeListener(e -> {
            if (isPopulating) return;
            double s = (Double) spnStart.getValue();
            double d = (Double) spnDuration.getValue();
            double stop = Math.round((s + d) * 10.0) / 10.0;
            spnStop.setValue(stop);
            saveToStep();
        });

        spnStop.addChangeListener(e -> {
            if (isPopulating) return;
            double s = (Double) spnStart.getValue();
            double stop = (Double) spnStop.getValue();
            if (stop <= s) {
                stop = s + 0.1;
                spnStop.setValue(stop);
            }
            double d = Math.max(0.1, Math.round((stop - s) * 10.0) / 10.0);
            spnDuration.setValue(d);
            saveToStep();
        });

        spnTransition.addChangeListener(e -> saveToStep());
        spnFadeOut.addChangeListener(e -> saveToStep());
    }

    private void saveToStep() {
        if (isPopulating || currentStep == null) return;

        currentStep.setSection(txtSection.getText().trim());
        currentStep.setName(txtName.getText().trim());
        currentStep.setTargetLayer(cmbLayer.getSelectedIndex());
        currentStep.setBlendMode((String) cmbBlend.getSelectedItem());

        int grpIdx = cmbFixtureGroup.getSelectedIndex();
        String targetGroup = switch (grpIdx) {
            case 1 -> "trusses";
            case 2 -> "festoon";
            case 3 -> "panels";
            case 4 -> "lamps";
            case 5 -> "projectors";
            default -> "all";
        };
        currentStep.setFixtureGroup(targetGroup);

        // Channels
        if (chkChAll.isSelected()) {
            currentStep.setChannels(null);
        } else {
            List<Integer> chs = new ArrayList<>();
            if (chkCh1.isSelected()) chs.add(1);
            if (chkCh2.isSelected()) chs.add(2);
            if (chkCh3.isSelected()) chs.add(3);
            if (chkCh4.isSelected()) chs.add(4);
            currentStep.setChannels(chs.isEmpty() ? null : chs);
        }

        currentStep.setPatternId((String) cmbPattern.getSelectedItem());
        currentStep.setPrimaryColor(txtColorHex.getText().trim());

        String pal = (String) cmbPalette.getSelectedItem();
        currentStep.setPalette(pal != null && !pal.startsWith("(") ? pal : null);

        currentStep.setSpeed((Double) spnSpeed.getValue());
        currentStep.setBrightness((Double) spnBrightness.getValue());

        currentStep.setStartTimeSec((Double) spnStart.getValue());
        currentStep.setDurationSec((Double) spnDuration.getValue());
        currentStep.setTransitionSec((Double) spnTransition.getValue());
        currentStep.setFadeOutSec((Double) spnFadeOut.getValue());
        currentStep.setTargetOpacity((Double) spnOpacity.getValue());

        if (currentRow != -1 && tableModel != null) {
            tableModel.fireTableRowsUpdated(currentRow, currentRow);
            tableModel.notifyStepModified();
        }
    }

    private void setEnabledAll(boolean enabled) {
        Component[] comps = {
                txtSection, cmbQuickSection, txtName, cmbLayer, cmbBlend, cmbFixtureGroup,
                chkChAll, chkCh1, chkCh2, chkCh3, chkCh4,
                cmbPattern, txtColorHex, btnColorPick, cmbPalette,
                sldSpeed, spnSpeed, sldBrightness, spnBrightness,
                spnStart, spnDuration, spnStop, spnTransition, spnFadeOut,
                sldOpacity, spnOpacity
        };
        for (Component c : comps) {
            c.setEnabled(enabled);
        }
    }

    private void updateColorButtonBackground(String hex) {
        Color c = parseColor(hex);
        btnColorPick.setBackground(c);
        btnColorPick.repaint();
    }

    public void updateCapabilities(com.wled.sequencer.client.EngineCapabilities caps) {
        if (caps == null) return;
        SwingUtilities.invokeLater(() -> {
            boolean wasPop = isPopulating;
            isPopulating = true;
            try {
                if (caps.patterns() != null && !caps.patterns().isEmpty()) {
                    String curPat = (String) cmbPattern.getSelectedItem();
                    cmbPattern.removeAllItems();
                    for (String p : caps.patterns()) {
                        cmbPattern.addItem(p);
                    }
                    if (curPat != null) cmbPattern.setSelectedItem(curPat);
                }

                if (caps.palettes() != null && !caps.palettes().isEmpty()) {
                    String curPal = (String) cmbPalette.getSelectedItem();
                    cmbPalette.removeAllItems();
                    cmbPalette.addItem("(None / Solid Primary)");
                    for (String pal : caps.palettes()) {
                        cmbPalette.addItem(pal);
                    }
                    if (curPal != null) cmbPalette.setSelectedItem(curPal);
                }
            } finally {
                isPopulating = wasPop;
            }
        });
    }

    private Color parseColor(String hex) {
        try {
            if (hex != null && hex.startsWith("#") && hex.length() == 7) {
                return Color.decode(hex);
            }
        } catch (Exception ignored) {}
        return Color.RED;
    }
}
