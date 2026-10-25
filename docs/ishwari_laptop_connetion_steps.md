Absolutely. Here is your CloudHeal Windows K3s Connection Guide. Save it somewhere outside your repository so you can reconnect your Mac to the Windows Kubernetes cluster whenever you need it.

You do not need to reinstall K3s or repeat the initial setup every time.

CloudHeal: Reconnect Mac to Windows Kubernetes

1. Start the Windows laptop

Make sure the Windows laptop is awake, connected to the internet, and running Tailscale.

Open Windows PowerShell and run:

tailscale status

Confirm both devices appear online:

* Windows: 100.86.103.118
* Mac: 100.90.104.13

If Tailscale is disconnected, reconnect it using the Tailscale application.

2. Start Ubuntu WSL2

Open Ubuntu from the Windows Start menu.

Check that K3s is running:

sudo systemctl status k3s

If it is inactive, start it:

sudo systemctl start k3s

Verify the node:

sudo k3s kubectl get nodes

Expected: desktop-dj20fek should show Ready.

Check the workload:

sudo k3s kubectl get deployments,pods -A

Your existing test workload should appear as cloudheal-pilot, with its pod running.

3. Check the Windows-to-WSL forwarding route

Open Windows PowerShell as Administrator.

Run:

netsh interface portproxy show all

You should see:

Listen address	Port	Forwarding address	Port
100.86.103.118	16443	172.18.15.70	6443

The WSL address 172.18.15.70 may change after a WSL restart. If it changes, the forwarding destination must be updated.

Check that the firewall rule exists:

Get-NetFirewallRule -DisplayName "CloudHeal K3s API from Mac"

The rule should remain enabled and restrict incoming connections to your Mac’s Tailscale IP, 100.90.104.13.

Security note: Keep port 16443 restricted to your Mac’s Tailscale address. Don’t create a broad inbound firewall rule for the Kubernetes API.

4. Connect from your Mac

Open Terminal on your MacBook.

Check Tailscale connectivity:

tailscale ping 100.86.103.118

A response such as pong from desktop-dj20fek indicates that the Tailscale peer is reachable. It may use a DERP relay rather than a direct connection.

Test the Kubernetes API:

curl -k -I --connect-timeout 5 https://100.86.103.118:16443

An HTTP response such as 401 Unauthorized confirms that the endpoint responds. It does not, by itself, verify authenticated Kubernetes access.

5. Verify Kubernetes access

Your Mac’s separate kubeconfig is stored at:

~/.kube/cloudheal-k3s.yaml

We already configured it to use:

https://100.86.103.118:16443

You don’t need to recreate it every time.

Run these commands on your Mac.

Check the cluster node:

kubectl --kubeconfig ~/.kube/cloudheal-k3s.yaml --request-timeout=10s get nodes

Check workloads:

kubectl --kubeconfig ~/.kube/cloudheal-k3s.yaml --request-timeout=10s get deployments,pods -A

Check resource usage:

kubectl --kubeconfig ~/.kube/cloudheal-k3s.yaml --request-timeout=10s top nodes

Expected result

Your Mac should see:

* Node: desktop-dj20fek
* Status: Ready
* Deployment: cloudheal-pilot
* Pod: Running
* CPU and memory metrics from the Windows WSL2 node

⸻

6. If the connection fails

Use this troubleshooting table.

Problem	What to check
Tailscale ping fails	Ensure Tailscale is running on both devices.
Kubernetes API times out	Check the Windows forwarding route and firewall rule.
K3s node is NotReady	Inspect K3s status in Ubuntu WSL2.
Forwarding uses an old WSL IP	Run hostname -I in Ubuntu and update the forwarding destination if needed.
TLS certificate error	Check the kubeconfig endpoint and the K3s API certificate SAN.
kubectl hangs	Retry with --request-timeout=10s and inspect the error.
Windows laptop sleeps	Wake it and verify K3s, WSL2, and Tailscale are running.

If the WSL IP changes

In Ubuntu WSL, run:

hostname -I

Identify the current WSL address used by K3s.

Then, in Administrator PowerShell, remove and recreate the forwarding entry using the new address:

netsh interface portproxy delete v4tov4 listenaddress=100.86.103.118 listenport=16443
netsh interface portproxy add v4tov4 listenaddress=100.86.103.118 listenport=16443 connectaddress=NEW_WSL_IP connectport=6443

Replace NEW_WSL_IP with the actual WSL IP. Keep the listener address, port, and restricted firewall rule unchanged.

7. Important: Keep your existing configurations

* Mac: Keep Docker Desktop Kubernetes and the separate ~/.kube/cloudheal-k3s.yaml configuration.
* Windows: Keep your existing Docker workloads and the K3s installation in Ubuntu WSL2.
* Credentials: Never commit cloudheal-k3s.yaml to GitHub or share its contents.
* CloudHeal repository: No source-code changes were required for this remote Kubernetes connection.

Quick reconnect checklist

When you return to CloudHeal, use this short sequence:

1. Start Windows and connect Tailscale.
2. Open Ubuntu WSL2 and check that K3s is running.
3. Verify the Windows port-forwarding route.
4. Open Mac Terminal and run tailscale ping 100.86.103.118.
5. Run kubectl --kubeconfig ~/.kube/cloudheal-k3s.yaml --request-timeout=10s get nodes.
6. Confirm the node is Ready.

One remaining issue: Your Mac and Windows currently communicate through Tailscale’s Bengaluru DERP relay, and we have observed occasional timeouts. The connection works, but we have not yet established a direct peer-to-peer connection or built a multi-node Kubernetes cluster.

That is where we can resume next time.