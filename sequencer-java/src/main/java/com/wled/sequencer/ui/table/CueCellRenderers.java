package com.wled.sequencer.ui.table;

import com.wled.sequencer.model.SequenceStep;
import com.wled.sequencer.player.TimelinePlayer;

import javax.swing.*;
import javax.swing.table.DefaultTableCellRenderer;
import java.awt.*;
import java.util.Set;

/**
 * Standard table cell renderer with Arial font and clean default highlights.
 */
public class CueCellRenderers extends DefaultTableCellRenderer {
    private static final Font FONT_REGULAR = new Font("Arial", Font.PLAIN, 12);
    private static final Font FONT_BOLD = new Font("Arial", Font.BOLD, 12);

    private static final Color PLAYING_BG = new Color(225, 238, 255);
    private static final Color PLAYING_FG = new Color(10, 45, 100);

    private final TimelinePlayer player;
    private final CueTableModel tableModel;

    public CueCellRenderers(TimelinePlayer player, CueTableModel tableModel) {
        this.player = player;
        this.tableModel = tableModel;
    }

    @Override
    public Component getTableCellRendererComponent(JTable table, Object value,
                                                   boolean isSelected, boolean hasFocus,
                                                   int row, int column) {
        super.getTableCellRendererComponent(table, value, isSelected, hasFocus, row, column);

        SequenceStep step = tableModel.getStepAt(row);
        boolean isPlayingRow = false;
        if (step != null && player != null && player.isPlaying()) {
            Set<String> activeIds = player.getActiveCueIds();
            isPlayingRow = activeIds.contains(step.getId());
        }

        if (isPlayingRow) {
            setBackground(PLAYING_BG);
            setForeground(PLAYING_FG);
            setFont(FONT_BOLD);
        } else if (isSelected) {
            setBackground(table.getSelectionBackground());
            setForeground(table.getSelectionForeground());
            setFont(FONT_REGULAR);
        } else {
            setBackground(table.getBackground());
            setForeground(table.getForeground());
            setFont(FONT_REGULAR);
        }

        // Alignments & formats
        if (value instanceof Number n) {
            if (column == 0 || column == 3) {
                // # or Layer
                setHorizontalAlignment(SwingConstants.CENTER);
                setText(column == 3 ? "L" + n.intValue() : n.toString());
            } else {
                // Seconds timing
                setHorizontalAlignment(SwingConstants.RIGHT);
                setText(String.format("%.1fs", n.doubleValue()));
            }
        } else if (column == 1) {
            // Section
            setHorizontalAlignment(SwingConstants.LEFT);
            setText(value != null ? "[" + value + "]" : "");
        } else if (column == 10) {
            // Target
            setHorizontalAlignment(SwingConstants.CENTER);
            setText(value != null ? value.toString() : "ALL");
        } else {
            setHorizontalAlignment(SwingConstants.LEFT);
            setText(value != null ? value.toString() : "");
        }

        setBorder(BorderFactory.createEmptyBorder(2, 4, 2, 4));
        return this;
    }
}
