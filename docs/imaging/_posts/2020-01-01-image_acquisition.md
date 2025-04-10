---
title: "Image Acquisition"
excerpt: "Image Acquisition"
layout: single

---

### Structural MRI

<table style="font-size: 12px;">
    <thead>
        <tr>
            <th>Study</th>
            <th>Sequence</th>
            <th>Scanner Type</th>
            <th>Voxel Size (mm)</th>
            <th>Image Orientation</th>
            <th>Parallel Reduction Factor in Plane</th>
            <th>TR (ms)</th>
            <th>TE (ms)</th>
            <th>Matrix Size (voxels)</th>
            <th>Flip Angle (deg)</th>
            <th>Dominant Group (%)</th>
        </tr>
    </thead>
    <tbody>
        {% for row in site.data.smri_studies %}
            <tr>
                <td>{{ row.study }}</td>
                <td>{{ row.sequence }}</td>
                <td>{{ row.scanner }}</td>
                <td>{{ row.voxel_size }}</td>
                <td>{{ row.orientation }}</td>
                <td>{{ row.inplane_acceleration }}</td>
                <td>{{ row.tr }}</td>
                <td>{{ row.te }}</td>
                <td>{{ row.matrix_size }}</td>
                <td>{{ row.flip_angle }}</td>
                <td>{{ row.perc_dominant }}</td>
            </tr>
        {% endfor %}
    </tbody>
</table>


### Functional MRI

<table style="font-size: 12px;">
    <thead>
        <tr>
            <th>Study</th>
            <th>Sequence</th>
            <th>Tasks</th>
            <th>Total Time (min:sec)</th>
            <th>Number of Volumes</th>
            <th>Scanner Type</th>
            <th>Voxel Size (mm)</th>
            <th>TR (ms)</th>
            <th>TE (ms)</th>
            <th>Matrix Size (voxels)</th>
            <th>Flip Angle (deg)</th>
            <th>Dominant Group (%)</th>
            <th>Field Map</th>
        </tr>
    </thead>
    <tbody>
        {% for row in site.data.fmri_studies %}
            <tr>
                <td>{{ row.study }}</td>
                <td>{{ row.sequence }}</td>
                <td>{{ row.tasks }}</td>
                <td>{{ row.duration }}</td>
                <td>{{ row.n_volumes }}</td>
                <td>{{ row.scanner }}</td>
                <td>{{ row.voxel_size }}</td>
                <td>{{ row.tr }}</td>
                <td>{{ row.te }}</td>
                <td>{{ row.matrix_size }}</td>
                <td>{{ row.flip_angle }}</td>
                <td>{{ row.perc_dominant }}</td>
                <td>{{ row.fmap }}</td>
            </tr>
        {% endfor %}
    </tbody>
</table>
