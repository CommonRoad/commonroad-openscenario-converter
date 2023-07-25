from osc_cr_converter.udp_driver.common import (
    UdpSender,
    OSIReceiver,
    base_port,
    input_modes,
)
import struct
import threading

run_thread = True


def receive():
    global data
    while run_thread:
        msg = osiReceiver.receive()
        for i, o in enumerate(msg.moving_object):
            print("Object[{}] id {}".format(i, o.id.value))
            print(
                "\t pos.x {:.2f} pos.y {:.2f} rot.h {:.2f}".format(
                    o.base.position.x, o.base.position.y, o.base.orientation.yaw
                )
            )
            print(
                "\t vel.x {:.2f} vel.y {:.2f} rot_rate.h {:.2f}".format(
                    o.base.velocity.x, o.base.velocity.y, o.base.orientation_rate.yaw
                )
            )
            print(
                "\t tacc.x {:.2f} acc.y {:.2f} rot_acc.h {:.2f}".format(
                    o.base.acceleration.x,
                    o.base.acceleration.y,
                    o.base.orientation_acceleration.yaw,
                )
            )
    print("ENDING THREAD")


if __name__ == "__main__":
    # Create UDP socket objects
    udp_sender = UdpSender(base_port + 0)
    osiReceiver = OSIReceiver()

    t1 = threading.Thread(target=receive)
    t1.start()
    print("WAITING TO START")
    osiReceiver.receive()
    print("STARTING PLANNER")

    done = False
    throttle = 0.0  # range in [0, 1]
    brake = 0.2  # range in [0, 1]
    steering = 0.0  # range in [0, 1]

    counter = 0
    object_id = 0  #

    while not done:
        udp_sender.send(
            struct.pack(
                "iiiiddd",
                1,  # version
                input_modes["driverInput"],
                object_id,  # object ID
                counter,  # frame nr
                throttle,  # throttle
                brake,  # brake
                steering,  # steering angle
            )
        )
        if KeyboardInterrupt:
            done = True
        print(
            "{} throttle {:.2f} brake {:.2f} steer_angle {:.2f}".format(
                counter, throttle, brake, steering
            )
        )

        counter += 1

        # close
        udp_sender.close()

    run_thread = False
