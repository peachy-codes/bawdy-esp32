package com.wled.sequencer.ui.table;

import com.wled.sequencer.model.SequenceData;
import com.wled.sequencer.model.SequenceStep;

import javax.swing.table.AbstractTableModel;
import java.util.List;

/**
 * Table model for the sequence cues table.
 */
public class CueTableModel extends AbstractTableModel {
    private static final String[] COLUMN_NAMES = {
            "#", "Section", "Cue Name", "Layer", "Start (s)", "Stop (s)", "Dur (s)",
            "Pattern", "Color/Palette", "Blend", "Target"
    };

    private SequenceData sequence;
    private Runnable onModifiedCallback;

    public CueTableModel(SequenceData sequence) {
        this.sequence = sequence != null ? sequence : new SequenceData("Show");
    }

    public void setOnModifiedCallback(Runnable callback) {
        this.onModifiedCallback = callback;
    }

    private void fireModified() {
        if (onModifiedCallback != null) {
            onModifiedCallback.run();
        }
    }

    public void notifyStepModified() {
        fireModified();
    }

    public void setSequence(SequenceData sequence) {
        this.sequence = sequence != null ? sequence : new SequenceData("Show");
        fireTableDataChanged();
    }

    public List<SequenceStep> getSteps() {
        return sequence.getSteps();
    }

    public SequenceStep getStepAt(int rowIndex) {
        if (rowIndex >= 0 && rowIndex < sequence.getSteps().size()) {
            return sequence.getSteps().get(rowIndex);
        }
        return null;
    }

    @Override
    public int getRowCount() {
        return sequence.getSteps().size();
    }

    @Override
    public int getColumnCount() {
        return COLUMN_NAMES.length;
    }

    @Override
    public String getColumnName(int column) {
        return COLUMN_NAMES[column];
    }

    @Override
    public Class<?> getColumnClass(int columnIndex) {
        return switch (columnIndex) {
            case 0, 3 -> Integer.class;
            case 4, 5, 6 -> Double.class;
            default -> String.class;
        };
    }

    @Override
    public boolean isCellEditable(int rowIndex, int columnIndex) {
        return false; // Edit through the inspector panel
    }

    @Override
    public Object getValueAt(int rowIndex, int columnIndex) {
        if (rowIndex < 0 || rowIndex >= sequence.getSteps().size()) return null;
        SequenceStep s = sequence.getSteps().get(rowIndex);
        return switch (columnIndex) {
            case 0 -> rowIndex + 1;
            case 1 -> s.getSection();
            case 2 -> s.getName();
            case 3 -> s.getTargetLayer();
            case 4 -> s.getStartTimeSec();
            case 5 -> s.getStopTimeSec();
            case 6 -> s.getDurationSec();
            case 7 -> s.getPatternId();
            case 8 -> s.getPalette() != null ? s.getPalette() : s.getPrimaryColor();
            case 9 -> s.getBlendMode();
            case 10 -> {
                String grp = s.getFixtureGroup();
                if (grp != null && !grp.isBlank() && !grp.equalsIgnoreCase("all")) {
                    yield grp.toUpperCase();
                }
                if (s.getChannels() != null && !s.getChannels().isEmpty()) {
                    yield "CH:" + s.getChannels().toString().replaceAll("[\\[\\] ]", "");
                }
                yield "ALL";
            }
            default -> null;
        };
    }

    public void addStep(SequenceStep step) {
        sequence.getSteps().add(step);
        int idx = sequence.getSteps().size() - 1;
        fireTableRowsInserted(idx, idx);
        fireModified();
    }

    public void duplicateStep(int index) {
        if (index < 0 || index >= sequence.getSteps().size()) return;
        SequenceStep orig = sequence.getSteps().get(index);
        SequenceStep copy = orig.clone();
        copy.setName(orig.getName() + " (Copy)");
        sequence.getSteps().add(index + 1, copy);
        fireTableRowsInserted(index + 1, index + 1);
        fireModified();
    }

    public void deleteStep(int index) {
        if (index < 0 || index >= sequence.getSteps().size()) return;
        sequence.getSteps().remove(index);
        fireTableRowsDeleted(index, index);
        fireModified();
    }

    public void moveStep(int index, int direction) {
        int target = index + direction;
        if (index < 0 || index >= sequence.getSteps().size()) return;
        if (target < 0 || target >= sequence.getSteps().size()) return;
        SequenceStep step = sequence.getSteps().remove(index);
        sequence.getSteps().add(target, step);
        fireTableDataChanged();
        fireModified();
    }
}
