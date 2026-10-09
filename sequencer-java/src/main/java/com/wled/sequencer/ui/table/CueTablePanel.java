package com.wled.sequencer.ui.table;

import com.wled.sequencer.model.SequenceStep;
import com.wled.sequencer.player.PlayerListener;
import com.wled.sequencer.player.TimelinePlayer;
import javax.swing.*;
import java.awt.*;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.util.Set;
import java.util.function.Consumer;

/**
 * Panel holding the Cue Sequence JTable and cue manipulation buttons.
 */
public class CueTablePanel extends JPanel {
    private final JTable table;
    private final CueTableModel tableModel;
    private final TimelinePlayer player;

    private final JButton btnAdd;
    private final JButton btnDup;
    private final JButton btnDel;
    private final JButton btnUp;
    private final JButton btnDown;

    private Consumer<SequenceStep> onStepSelected;

    public CueTablePanel(CueTableModel tableModel, TimelinePlayer player) {
        this.tableModel = tableModel;
        this.player = player;

        setLayout(new BorderLayout(4, 4));
        setBorder(BorderFactory.createTitledBorder("Step Timeline (Cue Sequence)"));

        this.table = new JTable(tableModel);
        this.table.setFont(new Font("Arial", Font.PLAIN, 12));
        this.table.getTableHeader().setFont(new Font("Arial", Font.BOLD, 12));
        this.table.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        this.table.setRowHeight(22);
        this.table.setShowGrid(true);
        this.table.setGridColor(new Color(230, 230, 230));

        CueCellRenderers renderer = new CueCellRenderers(player, tableModel);
        for (int i = 0; i < table.getColumnCount(); i++) {
            table.getColumnModel().getColumn(i).setCellRenderer(renderer);
        }

        // Column widths
        int[] widths = {35, 75, 140, 45, 60, 60, 60, 80, 100, 80, 50};
        for (int i = 0; i < widths.length && i < table.getColumnCount(); i++) {
            table.getColumnModel().getColumn(i).setPreferredWidth(widths[i]);
        }

        JScrollPane scrollPane = new JScrollPane(table);
        scrollPane.setBorder(BorderFactory.createLineBorder(new Color(210, 210, 210), 1));
        add(scrollPane, BorderLayout.CENTER);

        // Action Toolbar
        JPanel actionPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 4));

        btnAdd = new JButton("Add Step");
        btnDup = new JButton("Duplicate");
        btnDel = new JButton("Delete");
        btnUp = new JButton("Move Up");
        btnDown = new JButton("Move Down");

        JButton[] buttons = {btnAdd, btnDup, btnDel, btnUp, btnDown};
        for (JButton b : buttons) {
            actionPanel.add(b);
        }
        add(actionPanel, BorderLayout.SOUTH);

        setupListeners();
        updateButtonStates();
    }

    public JTable getTable() {
        return table;
    }

    public void setOnStepSelected(Consumer<SequenceStep> onStepSelected) {
        this.onStepSelected = onStepSelected;
    }

    public SequenceStep getSelectedStep() {
        int row = table.getSelectedRow();
        return tableModel.getStepAt(row);
    }

    public void selectRow(int row) {
        if (row >= 0 && row < tableModel.getRowCount()) {
            table.setRowSelectionInterval(row, row);
            table.scrollRectToVisible(table.getCellRect(row, 0, true));
        }
    }

    private void setupListeners() {
        table.getSelectionModel().addListSelectionListener(e -> {
            if (!e.getValueIsAdjusting()) {
                updateButtonStates();
                int row = table.getSelectedRow();
                if (onStepSelected != null) {
                    onStepSelected.accept(tableModel.getStepAt(row));
                }
            }
        });

        table.addMouseListener(new MouseAdapter() {
            @Override
            public void mouseClicked(MouseEvent e) {
                if (e.getClickCount() == 2) {
                    int row = table.getSelectedRow();
                    if (row != -1 && player != null) {
                        player.jumpToStep(row);
                    }
                }
            }
        });

        btnAdd.addActionListener(e -> addNewStep());
        btnDup.addActionListener(e -> duplicateSelectedStep());
        btnDel.addActionListener(e -> deleteSelectedStep());
        btnUp.addActionListener(e -> moveStepUp());
        btnDown.addActionListener(e -> moveStepDown());

        if (player != null) {
            player.addListener(new PlayerListener() {
                @Override
                public void onPlaybackTick(double elapsedSec, double totalDurationSec, int activeCount) {
                    SwingUtilities.invokeLater(table::repaint);
                }

                @Override
                public void onActiveCuesChanged(Set<String> activeCueIds) {
                    SwingUtilities.invokeLater(table::repaint);
                }

                @Override
                public void onPlaybackStateChanged(boolean isPlaying, boolean isPaused) {
                    SwingUtilities.invokeLater(table::repaint);
                }
            });
        }
    }

    public void addNewStep() {
        double start = 0.0;
        String section = "Main";
        int layer = 0;
        if (tableModel.getRowCount() > 0) {
            SequenceStep last = tableModel.getStepAt(tableModel.getRowCount() - 1);
            start = last.getStopTimeSec();
            section = last.getSection();
            layer = (last.getTargetLayer() + 1) % 10;
        }
        SequenceStep newStep = new SequenceStep(
                "step_" + System.currentTimeMillis(),
                "Cue " + (tableModel.getRowCount() + 1),
                section,
                layer,
                start,
                4.0,
                "rainbow"
        );
        tableModel.addStep(newStep);
        selectRow(tableModel.getRowCount() - 1);
    }

    public void duplicateSelectedStep() {
        int row = table.getSelectedRow();
        if (row != -1) {
            tableModel.duplicateStep(row);
            selectRow(row + 1);
        }
    }

    public void deleteSelectedStep() {
        int row = table.getSelectedRow();
        if (row != -1 && tableModel.getRowCount() > 1) {
            tableModel.deleteStep(row);
            int nextSel = Math.min(row, tableModel.getRowCount() - 1);
            selectRow(nextSel);
        }
    }

    public void moveStepUp() {
        int row = table.getSelectedRow();
        if (row > 0) {
            tableModel.moveStep(row, -1);
            selectRow(row - 1);
        }
    }

    public void moveStepDown() {
        int row = table.getSelectedRow();
        if (row != -1 && row < tableModel.getRowCount() - 1) {
            tableModel.moveStep(row, 1);
            selectRow(row + 1);
        }
    }

    private void updateButtonStates() {
        int row = table.getSelectedRow();
        int count = tableModel.getRowCount();
        btnDup.setEnabled(row != -1);
        btnDel.setEnabled(row != -1 && count > 1);
        btnUp.setEnabled(row > 0);
        btnDown.setEnabled(row != -1 && row < count - 1);
    }
}
