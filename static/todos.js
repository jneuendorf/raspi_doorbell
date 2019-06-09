import React, {Component} from "react"
import {render} from "react-dom"
import {sortableContainer, sortableElement, sortableHandle} from "react-sortable-hoc"
import array_move from "array-move"


const DragHandle = sortableHandle(() => <div className="Showcase__style__handle" />)

const SortableItem = sortableElement(({value, index, delete_item}) => <div
    className="Showcase__style__item Showcase__style__stylizedItem"
    style={{height: 59}}
>
    <DragHandle/> {value}
    <button
        className="btn btn-danger"
        style={{
            fontSize: 30,
            height: 48,
            paddingTop: 4,
            position: "absolute",
            right: 4,
            textAlign: "center",
            width: 48,
        }}
        onClick={() => delete_item(index)}
    >
        &times;
    </button>
</div>)

const SortableContainer = sortableContainer(({children}) => {
    return <div
        className="Showcase__style__list Showcase__style__stylizedList"
    >
        {children}
    </div>
})

class App extends Component {
    constructor(props) {
        super(props)
        this.state = {
            todos: globals.todos.slice(0),
            last_saved_todos: globals.todos.slice(0),
        }

        this.on_sort_end = this.on_sort_end.bind(this)
        this.append_item = this.append_item.bind(this)
        this.delete_item = this.delete_item.bind(this)
        this.undo = this.undo.bind(this)
        this.save = this.save.bind(this)
    }

    on_sort_end({oldIndex, newIndex}) {
        this.setState(({todos}) => ({
            todos: array_move(todos, oldIndex, newIndex)
        }))
    }

    append_item() {
        const value = prompt("Neues Todo")
        if (value) {
            const {todos} = this.state
            this.setState({todos: todos.concat([value])})
        }
    }

    delete_item(index) {
        const {todos} = this.state
        this.setState({todos: todos.filter((_, i) => i !== index)})
    }

    undo() {
        const {last_saved_todos} = this.state
        this.setState({todos: last_saved_todos})
    }

    save() {
        const {todos} = this.state
        fetch("/todos", {
            method: "post",
            headeres: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(todos),
        }).then(response => {
            console.log(response)
            if (response.ok) {
                alert("Erfolgreich gespeichert!")
                this.setState({last_saved_todos: todos.slice(0)})
            }
            else {
                alert("Fehler beim Speichern!")
            }
        })
    }

    render() {
        const {todos} = this.state

        return <div className="Showcase__Content__root">
            <div className="Showcase__Content__wrapper">
                <h1>Todos</h1>
                <SortableContainer
                    onSortEnd={this.on_sort_end}
                    useDragHandle
                    className="Showcase__style__list Showcase__style__stylizedList"
                    helperClass="Showcase__style__stylizedHelper"
                    itemClass="Showcase__style__item Showcase__style__stylizedItem"
                >
                    {
                        todos.map((value, index) => <SortableItem
                            key={`item-${index}`}
                            index={index}
                            value={value}
                            delete_item={this.delete_item}
                        />)
                    }
                    <button
                        className="btn btn-primary"
                        style={{fontSize: 18, marginTop: "0.5em"}}
                        onClick={this.append_item}
                        dangerouslySetInnerHTML={{__html: "&plus;"}}
                    />
                </SortableContainer>
                <button
                    className="btn btn-primary btn-lg"
                    style={{marginTop: "1em"}}
                    onClick={this.save}
                >
                    Speichern
                </button>
                &nbsp;
                <button
                    className="btn btn-default btn-lg"
                    style={{marginTop: "1em"}}
                    onClick={this.undo}
                >
                    Rückgängig
                </button>
            </div>
        </div>
    }
}

render(<App/>, document.querySelector(".mount-point"))
