import React from 'react'
import {
    // AsyncStorage,
    Button,
    Dimensions,
    Image,
    KeyboardAvoidingView,
    Slider,
    StyleSheet,
    Text,
    TextInput,
    TouchableWithoutFeedback,
    View,
} from 'react-native'

import messageTypes from '../websocket-message-types'
import serverConfig from '../server-config'

// <div>Icons made by <a href="https://www.flaticon.com/authors/smashicons" title="Smashicons">Smashicons</a> from <a href="https://www.flaticon.com/" 			    title="Flaticon">www.flaticon.com</a> is licensed by <a href="http://creativecommons.org/licenses/by/3.0/" 			    title="Creative Commons BY 3.0" target="_blank">CC 3.0 BY</a></div>


console.log(messageTypes)

const RGB_RAW = '70, 142, 249'
const RGB = `rgb(${RGB_RAW})`
const RGB_ERROR = 'rgb(255, 0, 0)'
// const RGBA = `rgba(${RGB_RAW}, 0.6)`
const SCREEN_WIDTH = Dimensions.get('window').width


export default class App extends React.PureComponent {
    websocket = null
    state = {
        host: null,
        volume: 1,
        isConnected: false,
        connectionError: null,
    }

    // constructor(props) {
    //     super(props)
    //     this.init()
    // }
    //
    // async init() {
    //     try {
    //         const host = await AsyncStorage.getItem('host')
    //         if (host) {
    //             console.log('using stored', host)
    //             this.setState({host})
    //         }
    //     }
    //     catch (error) {
    //         console.error(error)
    //     }
    // }

    updateHost = text => {
        this.setState({host: text})
    }

    connect = () => {
        if (this.websocket) {
            this.disconnect()
        }

        return new Promise((resolve, reject) => {
            const {host} = this.state
            let websocket
            try {
                websocket = new WebSocket(`ws://${host}/websocket`)
                // websocket = new WebSocket(`wss://echo.websocket.org`)
                this.websocket = websocket
            }
            catch (error) {
                reject(error)
            }
            websocket.onopen = async () => {
                resolve()
                this.setState({isConnected: true})
                // // Connection successful so we save the host.
                // try {
                //     await AsyncStorage.setItem('host', host)
                // }
                // catch (error) {
                //     console.error(error)
                // }
                    this.send({type: messageTypes.requestVolume})
            }
            websocket.onmessage = (event) => {
                this.handleMessage(event.data)
            }
            websocket.onerror = (error) => {
                reject(error)
                // console.error(error)
            }
            websocket.onclose = (event) => {
                console.log(event.code, event.reason)
                reject(event)
                this.setState({isConnected: false})
            }
        })
    }

    disconnect = () => {
        this.websocket.close()
        this.websocket = null
    }

    tryConnecting = async () => {
        try {
            await this.connect()
        }
        catch (error) {
            console.log(error)
            this.setState({connectionError: error})
        }
    }

    send(message) {
        const {websocket} = this
        if (websocket) {
            console.log('sending', message)
            websocket.send(JSON.stringify(message))
        }
        else {
            console.warn('No open websocket!')
        }
    }

    handleMessage(message) {
        try {
            message = JSON.parse(message)
        }
        catch (error) {
            console.log('received invalid message', message)
            message = null
        }
        if (message) {
            const {type, ...payload} = message
            if (type === messageTypes.receiveVolume) {
                this.setState(payload)
            }
            else if (type === messageTypes.receiveBell) {
                alert('Ring')
            }
        }
    }

    setVolume = volume => {
        this.setState({volume})
        this.send({type: messageTypes.updateVolume, volume})
    }

    hideKeyboard = () => {
        if (this.input) {
            this.input.blur()
        }
    }

    setInputRef = element => {
        this.input = element
    }

    //=========================================================================
    // React Lifecycle methods.
    async componentDidMount() {
        if (this.state.host) {
            try {
                this.connect()
            }
            catch (error) {
                this.setState({connectionError: error})
            }
        }
    }

    render() {
        const {host, volume, isConnected, connectionError} = this.state
        console.log(this.state)

        return <KeyboardAvoidingView
            behavior="padding"
            style={styles.container}
        >
            <TouchableWithoutFeedback onPress={this.hideKeyboard}>
                <View style={styles.logoSection}>
                    <Image
                        source={
                            isConnected
                            ? require(`./assets/icon_small_active.png`)
                            : require(`./assets/icon_small_inactive.png`)
                        }
                        style={styles.logo}
                    />
                </View>
            </TouchableWithoutFeedback>

            <View style={styles.section}>
                <Text>Host</Text>
                <TextInput
                    ref={this.setInputRef}
                    returnKeyType="go"
                    value={host}
                    autoCapitalize="none"
                    autoCorrect={false}
                    placeholder={`192.168.1.111:${serverConfig.port}`}
                    placeholderTextColor="rgb(139, 139, 139)"
                    underlineColorAndroid={connectionError ? RGB_ERROR : RGB}
                    style={[
                        styles.ipBase,
                        connectionError ? styles.ipError : styles.ip,
                    ]}
                    onChangeText={this.updateHost}
                />
                {
                    isConnected
                    ? <Button
                        title="Disonnect"
                        color={RGB}
                        onPress={this.disconnect}
                    />
                    : <Button
                        title="Connect"
                        color={RGB}
                        onPress={this.tryConnecting}
                    />
                }
            </View>

            <TouchableWithoutFeedback onPress={this.hideKeyboard}>
                <View style={styles.section}>
                    <Text>Volume</Text>
                    <Slider
                        minimumValue={0}
                        maximumValue={1}
                        value={volume}
                        style={styles.slider}
                        onSlidingComplete={this.setVolume}
                        // disabled={!isConnected}
                    />
                </View>
            </TouchableWithoutFeedback>
        </KeyboardAvoidingView>
    }
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: 'white',
        width: SCREEN_WIDTH,
    },
    logoSection: {
        paddingTop: 50,
        justifyContent: 'center',
        alignItems: 'center',
        borderBottomWidth: StyleSheet.hairlineWidth,
        borderBottomColor: RGB,
        width: SCREEN_WIDTH,
    },
    section: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        borderBottomWidth: StyleSheet.hairlineWidth,
        borderBottomColor: RGB,
        width: SCREEN_WIDTH,
    },
    logo: {
        width: 150,
        height: 150,
    },
    ipBase: {
        fontWeight: 'bold',
        fontSize: 28,
        textAlign: 'center',
        width: SCREEN_WIDTH * 0.8,
    },
    ip: {
        color: RGB,
    },
    ipError: {
        color: RGB_ERROR,
    },
    slider: {
        height: 35,
        width: SCREEN_WIDTH * 0.8
    },
})
