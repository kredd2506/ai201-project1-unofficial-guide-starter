# GPU Pods

Source: https://nrp.ai/documentation/userdocs/running/gpu-pods

Note — Note:

In this section you will request GPUs. Make sure you don’t waste those and delete your pods when not using the GPUs.

Note — Caution:

Some specific high-memory GPUs require the gpu type specified in the container `resource` requests and limits. See [Requesting special GPUs](#requesting-special-gpus)

## Running GPU pods

Use this definition to create your own pod and deploy it to kubernetes:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-pod-example
spec:
  containers:
  - name: gpu-container
    image: tensorflow/tensorflow:latest-gpu
    command: ["sleep", "infinity"]
    resources:
      limits:
        nvidia.com/gpu: 1
      requests:
        nvidia.com/gpu: 1
```

This example requests 1 GPU device. You can have up to 8 per node if you’re [using jobs](/documentation/userdocs/running/jobs/), and up to 2 for pods. If you request GPU devices in your pod, kubernetes will auto schedule your pod to the appropriate node. There’s no need to specify the location manually.

Note — You should always delete your pod when your computation is done to let other users use the GPUs.:

Consider using [Jobs](/documentation/userdocs/running/jobs/) **with actual script instead of `sleep`** whenever possible to ensure your pod is not wasting GPU time. If you have never used Kubernetes before, see the [tutorial](/documentation/userdocs/tutorial/introduction/).

## Requesting special GPUs

Certain kinds of GPUs are advertised on nodes as a special resource, f.e. “nvidia.com/rtx-8000”. You have to request that resource instead of the “nvidia.com/gpu” one.

The current list is:

| GPU Type | Resource |
| --- | --- |
| NVIDIA A40 | nvidia.com/a40 |
| NVIDIA A100 | nvidia.com/a100 |
| NVIDIA RTX A6000 | nvidia.com/rtxa6000 |
| NVIDIA Quadro RTX 8000 | nvidia.com/rtx8000 |
| NVIDIA H100 | nvidia.com/h100 |
| NVIDIA H200 | nvidia.com/h200 |
| NVIDIA RTX PRO 6000 Blackwell | nvidia.com/rtx6000bw |
| NVIDIA GH200 Grace Hopper | nvidia.com/gh200 |
| NVIDIA A100 MIG 1g.10gb | nvidia.com/mig-small |

Note — Access policy for A100 / H100 / H200 / GH200:

These four GPU types are gated by a per-namespace ResourceQuota. By default every namespace has a quota of **zero** for each of them. To run a pod on one of them you have one of these paths:

- **NVIDIA A100** — user-requestable. Submit the [A100 access request](/reservations) and an admin will raise your namespace’s a100 quota.
- **NVIDIA H100, H200, and GH200** — **not user-requestable.** These are reserved for the groups that contributed the hardware, plus LLM workloads consuming spare cycles. There is no access form.
- **Any user, any of the four GPUs, no reservation** — set `priorityClassName: opportunistic` (or `opportunistic2`) on your pod. The quota does not apply to opportunistic-tier pods, but they can be preempted by any other pod at any time. See [Priority Classes](/documentation/userdocs/running/priority-classes/) for details and a full example.
For example, modifying the above example for one of these GPUs, the new yaml would be:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-pod-example
spec:
  containers:
  - name: gpu-container
    image: tensorflow/tensorflow:latest-gpu
    command: ["sleep", "infinity"]
    resources:
      limits:
        nvidia.com/a100: 1
      requests:
        nvidia.com/a100: 1
```

For Grace Hopper node make sure you’re also using the image with `arm` support (`nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04` is a good one) and [tolerating the arm64 architecture](/documentation/userdocs/running/special/):

```yaml
tolerations:
- key: "nautilus.io/arm64"
  operator: "Exists"
  effect: "NoSchedule"
```

For RTX PRO 6000 Blackwell nodes, request the dedicated resource:

```yaml
resources:
  limits:
    nvidia.com/rtx6000bw: 1
  requests:
    nvidia.com/rtx6000bw: 1
```

## Requesting many GPUs

Since 1 and 2 GPU jobs are blocking nodes from getting 4 and 8-GPU jobs, there are some nodes reserved for those. Once you submit a job with 4 or 8 GPUs request, a controller will automatically add toleration which will allow you to use the node reserved for more GPUs. You don’t need to do anything manually for that.

## Choosing GPU type

**See [requesting special GPUs](#requesting-special-gpus) for special types of GPU**

We have a variety of GPU flavors attached to Nautilus. This table describes the types of GPUs available for use, but is not up to date - it’s better to use the actual cluster information (f.e. `kubectl get nodes -L nvidia.com/gpu.product`).

Credit: [GPU types by NRP Nautilus](https://observablehq.com/d/7c0f46855b4212e0)

If you need more graphical memory, use this table or official specs to choose the type:

| GPU Type | Memory Size (GB) |
| --- | --- |
| NVIDIA GeForce GTX 1070 | 8 |
| NVIDIA GeForce GTX 1080 | 8 |
| NVIDIA Quadro M4000 | 8 |
| NVIDIA A100 MIG 2g.10gb | 10 |
| NVIDIA GeForce GTX 1080 Ti | 12 |
| NVIDIA GeForce RTX 2080 Ti | 12 |
| NVIDIA TITAN Xp | 12 |
| NVIDIA Tesla T4 | 16 |
| NVIDIA A10 | 24 |
| NVIDIA GeForce RTX 3090 | 24 |
| NVIDIA GeForce RTX 4090 | 24 |
| NVIDIA TITAN RTX | 24 |
| NVIDIA RTX A5000 | 24 |
| NVIDIA Quadro RTX 6000 | 24 |
| NVIDIA Tesla V100 SXM2 | 32 |
| NVIDIA A40 | 48 |
| NVIDIA L40 | 48 |
| NVIDIA RTX A6000 | 48 |
| NVIDIA Quadro RTX 8000 | 48 |
| NVIDIA A100 SXM4 | 80 |
| NVIDIA H200 NVL | 141 |

Note — Note:

[Not all nodes are available to all users](/documentation/userdocs/running/special/). You can consult about your available resources in [Matrix](https://nrp.ai/contact) and on [resources page](https://nrp.ai/viz/resources). Labs connecting their hardware to our cluster have preferential access to all our resources.

Note — Caution:

For higher memory GPUs, use the [requesting special GPUs syntax](#requesting-special-gpus)! Affinity allows you to further refine the GPU type or choose the GPU type for generic GPUs.

To use a **specific type of GPU**, add the affinity definition to you pod yaml file. The example below specifies *1080Ti* GPU:

```yaml
spec:
 affinity:
   nodeAffinity:
     requiredDuringSchedulingIgnoredDuringExecution:
       nodeSelectorTerms:
       - matchExpressions:
         - key: nvidia.com/gpu.product
           operator: In
           values:
           - NVIDIA-GeForce-GTX-1080-Ti
```

**To make sure you did everything correctly** after you’ve submited the job, look at the corresponding pod yaml (`kubectl get pod ... -o yaml`) and check that resulting nodeAffinity is as expected.

## Selecting CUDA version

In general the higher CUDA versions support the lower and same driver version. The nodes are labelled with the major and minor CUDA and driver versions. You can check those at the [resources page](https://nrp.ai/viz/resources) or list with this command (it will also choose only GPU nodes):

```bash
kubectl get nodes -L nvidia.com/cuda.driver.major,nvidia.com/cuda.driver.minor,nvidia.com/cuda.runtime.major,nvidia.com/cuda.runtime.minor -l nvidia.com/gpu.product
```

If you’re using the container image with higher CUDA version, you have to pick the nodes supporting it. Example:

```yaml
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: nvidia.com/cuda.runtime.major
            operator: In
            values:
            - "12"
          - key: nvidia.com/cuda.runtime.minor
            operator: In
            values:
            - "2"
```

Also you can choose the driver above something if you know which one you need (this will pick drivers **above** 535):

```yaml
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: nvidia.com/cuda.driver.major
            operator: Gt
            values:
            - "535"
```

## Adding Shared Memory (shm)

Note — Adding Shared Memory (shm):

You can add Shared Memory (shm) to your GPU pods in YAML:

```YAML
        volumeMounts:
        - mountPath: /dev/shm
          name: dshm
      volumes:
      - name: dshm
        emptyDir:
          medium: Memory
          sizeLimit: 2Gi
```

`sizeLimit` is an optional term. Otherwise it defaults to half of the memory request. Not adding /dev/shm defaults to 64MB.
