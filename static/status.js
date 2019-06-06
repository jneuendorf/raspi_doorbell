import React from "react"
import ReactDom from "react-dom"
import Switch from "react-switch"
import Slider from "rc-slider/lib/Slider"


const Seperator = () => {
    return <div style={{marginTop: 35, marginBottom: 35, borderTop: "1px solid gray"}} />
}


const styles = {
    slider: {
        handle: {
            height: 28,
            width: 28,
            marginLeft: -14,
            marginTop: -9,
        },
        handle_init: {
            display: "none",
        },
        track: {height: 10},
        rail: {height: 10},
    },
}


class StatusApp extends React.Component {
    constructor(props) {
        super(props)
        this.state = {
            do_not_disturb: globals.do_not_disturb_mode_is_on,
            volume: -1,
            restart_btn: {
                label: "Neu starten",
                disabled: false,
            },
        }

        this.init_websocket()

        this.restart_server = this.restart_server.bind(this)
        this.change_volume = this.change_volume.bind(this)
    }

    init_websocket() {
        const websocket = new WebSocket(`ws://${location.host}${globals.websocket_url}`)
        websocket.onopen = () => {
            websocket.send(JSON.stringify({type: globals.message_types.request_volume}))
        }
        websocket.onmessage = (event) => {
            this.handle_websocket_message(event.data)
        }
        websocket.onerror = (error) => {
            console.error(error)
        }
        websocket.onclose = (event) => {
            console.log(event.code, event.reason)
        }
    }

    handle_websocket_message(raw_message) {
        let message
        try {
            message = JSON.parse(raw_message)
        }
        catch (error) {
            console.log("received invalid message", raw_message)
            message = null
        }
        if (message) {
            const {type, ...payload} = message
            if (type === globals.message_types.receive_volume) {
                this.setState({volume: payload.volume})
            }
            /* else if (type === globals.message_types.receive_bell) {
                alert("Ring")
            } */
        }
    }

    render() {
        const {volume} = this.state

        return <div style={{margin: "0 auto", width: "80%"}}>
            <h2>Nicht-Stören-Modus</h2>
            <Switch
                disabled={true}
                checked={this.state.do_not_disturb}
                onChange={() => {}}
            />

            <Seperator />

            <h2>Volume</h2>
            <div style={{margin: 12}}>
                <Slider
                    min={0}
                    max={1}
                    step={0.01}
                    value={volume}
                    onAfterChange={this.change_volume}
                    handleStyle={
                        volume >= 0
                        ? styles.slider.handle
                        : styles.slider.handle_init
                    }
                    trackStyle={styles.slider.track}
                    railStyle={styles.slider.rail}
                />
            </div>

            {/* <Seperator />

            <button
                type="button"
                className="btn btn-lg btn-primary"
                onClick={this.restart_server}
                disabled={this.state.restart_btn.disabled}
            >
                {this.state.restart_btn.label}
            </button> */}

            <Seperator />

            <div style={{maxHeight: 200, overflow: "scroll", }}>
                {globals.bell_log.map(entry =>
                    // Because e.g. quotes are escaped in the log.
                    <pre dangerouslySetInnerHTML={{__html: entry}} />
                )}

            </div>
        </div>
    }

    change_volume(value) {
        const volume = parseFloat(value)
        this.setState({volume})
        websocket.send(JSON.stringify({
            type: globals.message_types.update_volume,
            volume,
        }))
    }

    restart_server() {
        this.setState({
            restart_btn: {
                label: "Wird neu gestartet...",
                disabled: true,
            },
        })
    }
}


ReactDom.render(
    <StatusApp />,
    document.querySelector(".mount-point")
)
